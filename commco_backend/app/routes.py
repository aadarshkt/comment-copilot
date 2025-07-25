import os
import functools
from flask import (
    Blueprint,
    jsonify,
    request,
    redirect,
    url_for,
    session,
    current_app,
    g,
)
from .models import db, User, Channel, Comment
from .services import encrypt_data, YouTubeService
from .tasks import process_channel_comments
import google_auth_oauthlib.flow
from google.oauth2 import credentials
import requests
from .logging_utils import (
    debug,
    info,
    warning,
    error,
    critical,
    exception,
    log_request,
    log_performance,
    log_auth_event,
    log_api_response,
)

import os

# THIS IS THE FIX:
# This line tells oauthlib that it's okay to use HTTP for local development.
# You MUST NOT use this in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Define the Blueprint for our API routes
main_bp = Blueprint("main", __name__, url_prefix="/api")


# --- Decorator for Protecting Routes ---
def login_required(f):
    """
    Ensures a user is logged in before allowing access to a route.
    Also loads the user object into Flask's global 'g' object.
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return jsonify({"error": "Unauthorized. Please log in."}), 401

        # Load the user object for the current request
        g.user = User.query.get(user_id)
        if g.user is None:
            # This case can happen if user was deleted but session persists
            session.clear()
            return jsonify({"error": "User not found. Session cleared."}), 401

        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================


@main_bp.route("/auth/google/login")
@log_request
def google_login():
    """
    Redirects the user to Google's OAuth consent screen.
    """
    debug("Starting Google OAuth login process")

    # Note: For production, use a more secure way to handle the client secrets file.
    # For now, we assume 'client_secret.json' is in the root directory.
    if not os.path.exists("client_secret.json"):
        error("Google client secret file not found", file_path="client_secret.json")
        return jsonify({"error": "Google client secret file not found on server."}), 500

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/youtube.force-ssl",  # More comprehensive scope for YouTube API
            "https://www.googleapis.com/auth/youtube.readonly",  # Fallback scope
            "openid",
        ],
        redirect_uri=url_for("main.google_callback", _external=True),
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",  # Gets a refresh token
        prompt="consent",  # Ensures user is prompted for permissions
    )
    session["state"] = state
    return redirect(authorization_url)


@main_bp.route("/auth/google/callback")
@log_request
def google_callback():
    """
    Handles the callback from Google after user grants permissions.
    Creates or updates the user, and establishes a session.
    """
    debug("Processing Google OAuth callback")

    state = session.get("state")
    if not state or state != request.args.get("state"):
        warning(
            "OAuth state mismatch",
            session_state=state,
            request_state=request.args.get("state"),
        )
        return jsonify({"error": "State mismatch. Invalid request."}), 400

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=None,  # to prevent CSRF
        state=state,
        redirect_uri=url_for("main.google_callback", _external=True),
    )

    # 'access_type=offline' is required to get a refresh token.
    # 'prompt=consent' forces the consent screen to appear every time,
    # ensuring a refresh token is issued (useful in development).
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    # Get user profile information
    try:
        user_info_response = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {creds.token}"},
        )
        if not user_info_response.ok:
            error(
                "Failed to fetch user info from Google",
                status_code=user_info_response.status_code,
                response_text=user_info_response.text,
            )
            return jsonify({"error": "Failed to fetch user info from Google."}), 500

        user_info = user_info_response.json()
        google_id = user_info["id"]
        info(
            "Successfully fetched user info from Google",
            google_id=google_id,
            email=user_info.get("email"),
        )
    except Exception as e:
        exception("Exception while fetching user info from Google", error=str(e))
        return jsonify({"error": "Failed to fetch user info from Google."}), 500

    # --- Find or Create User in our Database ---
    user = User.query.filter_by(google_id=google_id).first()

    encrypted_access_token = encrypt_data(creds.token)
    encrypted_refresh_token = (
        encrypt_data(creds.refresh_token) if creds.refresh_token else None
    )

    if user:
        # User exists, update their tokens
        info("Updating existing user", user_id=user.id, email=user.email)
        user.access_token_encrypted = encrypted_access_token
        if encrypted_refresh_token:
            user.refresh_token_encrypted = encrypted_refresh_token
    else:
        # New user: create a new record
        info("Creating new user", google_id=google_id, email=user_info["email"])
        user = User(
            google_id=google_id,
            email=user_info["email"],
            access_token_encrypted=encrypted_access_token,
            refresh_token_encrypted=encrypted_refresh_token,
        )
        db.session.add(user)
        db.session.flush()  # Flush

        # Also fetch and create their primary YouTube Channel
    if not user.channels or len(user.channels) == 0:
        try:
            debug("Fetching user's YouTube channels")
            yt_service = YouTubeService(credentials=creds)
            channels_data = yt_service.get_user_channels()
            if channels_data:
                # For MVP, we just take the first channel_data[0]
                channel_data = channels_data[0]
                info(
                    "Creating new YouTube channel",
                    channel_id=channel_data["id"],
                    user_id=user.id,
                )
                new_channel = Channel(
                    youtube_channel_id=channel_data["id"], user_id=user.id
                )
                db.session.add(new_channel)
            else:
                warning("No YouTube channels found for user", user_id=user.id)
        except Exception as e:
            error(
                "Failed to fetch/create YouTube channel", user_id=user.id, error=str(e)
            )

    try:
        db.session.commit()
        info("Database transaction committed successfully", user_id=user.id)
    except Exception as e:
        error("Database commit failed", user_id=user.id, error=str(e))
        db.session.rollback()
        raise

    # Log the user in by storing their DB id in the session
    session.clear()
    session["user_id"] = user.id

    log_auth_event("login_successful", user_email=user.email, user_id=user.id)

    # Redirect to the frontend dashboard
    return redirect(
        os.getenv("FRONTEND_URL", "http://localhost:3000/dashboard/comments")
    )


@main_bp.route("/auth/logout", methods=["POST"])
@login_required
@log_request
def logout():
    """
    Logs the user out by clearing the session.
    """
    log_auth_event("logout", user_email=g.user.email, user_id=g.user.id)
    session.clear()
    return jsonify({"message": "Successfully logged out."}), 200


# =================
# USER & APP ROUTES
# =============================================================================


@main_bp.route("/user/me")
@login_required
@log_request
def get_current_user():
    """
    Returns basic information about the currently logged-in user.
    Useful for the frontend to confirm login status.
    """
    debug("Fetching current user info", user_id=g.user.id)
    response_data = {
        "id": g.user.id,
        "email": g.user.email,
        "channel_id": (
            g.user.channels[0].youtube_channel_id if g.user.channels else None
        ),
    }
    return jsonify(response_data)


@main_bp.route("/channel/sync", methods=["POST"])
@login_required
@log_request
def sync_channel():
    """
    Triggers a background job to fetch and classify the latest comments for the user's channel.
    """
    if not g.user.channels:
        warning("Channel sync requested but no channel found", user_id=g.user.id)
        return jsonify({"error": "No YouTube channel linked to this account."}), 404

    channel = g.user.channels[0]
    info(
        "Starting channel sync",
        user_id=g.user.id,
        channel_id=channel.id,
        youtube_channel_id=channel.youtube_channel_id,
    )

    try:
        process_channel_comments.delay(channel.id)
        info(
            "Channel sync task queued successfully",
            user_id=g.user.id,
            channel_id=channel.id,
        )
        return jsonify({"message": "Channel sync has been started."}), 202
    except Exception as e:
        error(
            "Failed to queue channel sync task",
            user_id=g.user.id,
            channel_id=channel.id,
            error=str(e),
        )
        return jsonify({"error": "Failed to start channel sync."}), 500


@main_bp.route("/comments")
@login_required
@log_request
def get_comments():
    """
    Fetches categorized comments from the database for the user's channel.
    Accepts a 'category' query parameter to filter results.
    """
    valid_categories = [
        "Reply to Question",
        "Appreciate Fan",
        "Ideas",
        "Criticisms",
        "Delete Junk",
        "Miscellaneous",
        "All",
    ]
    category_filter = request.args.get("category", "All")

    debug("Fetching comments", user_id=g.user.id, category=category_filter)

    if category_filter not in valid_categories:
        warning(
            "Invalid category requested",
            category=category_filter,
            valid_categories=valid_categories,
            user_id=g.user.id,
        )
        return (
            jsonify({"error": f"Invalid category. Must be one of {valid_categories}"}),
            400,
        )

    if not g.user.channels:
        warning("Comments requested but no channel found", user_id=g.user.id)
        return jsonify({"error": "No YouTube channel linked to this account."}), 404

    channel = g.user.channels[0]

    try:
        # Handle "All" category by not filtering by category
        if category_filter == "All":
            comments = (
                Comment.query.filter_by(channel_id=channel.id)
                .order_by(Comment.published_at.desc())
                .limit(100)
                .all()
            )
        else:
            comments = (
                Comment.query.filter_by(channel_id=channel.id, category=category_filter)
                .order_by(Comment.published_at.desc())
                .limit(100)
                .all()
            )
        result = [
            {
                "id": c.id,
                "youtube_comment_id": c.youtube_comment_id,
                "text_original": c.text_original,
                "author_name": c.author_name,
                "author_avatar_url": c.author_avatar_url,
                "video_id": c.video_id,
                "published_at": c.published_at.isoformat(),
                "category": c.category,
            }
            for c in comments
        ]

        info(
            "Comments fetched successfully",
            user_id=g.user.id,
            channel_id=channel.id,
            category=category_filter,
            count=len(result),
        )

        return jsonify(result)

    except Exception as e:
        error(
            "Failed to fetch comments",
            user_id=g.user.id,
            channel_id=channel.id,
            category=category_filter,
            error=str(e),
        )
        return jsonify({"error": "Failed to fetch comments."}), 500


@main_bp.route("/comments/<int:comment_id>/reply", methods=["POST"])
@login_required
@log_request
def reply_to_comment(comment_id):
    """
    Reply to a specific comment using the YouTube API.
    """
    debug("Processing reply to comment", user_id=g.user.id, comment_id=comment_id)

    # Get the reply text from the request
    data = request.get_json()
    if not data or "reply_text" not in data:
        warning(
            "Missing reply_text in request", user_id=g.user.id, comment_id=comment_id
        )
        return jsonify({"error": "Missing reply_text in request body."}), 400

    reply_text = data["reply_text"].strip()
    if not reply_text:
        warning("Empty reply text", user_id=g.user.id, comment_id=comment_id)
        return jsonify({"error": "Reply text cannot be empty."}), 400

    # Check if user has a channel
    if not g.user.channels:
        warning("Reply requested but no channel found", user_id=g.user.id)
        return jsonify({"error": "No YouTube channel linked to this account."}), 404

    channel = g.user.channels[0]

    # Find the comment in our database
    comment = Comment.query.filter_by(id=comment_id, channel_id=channel.id).first()
    if not comment:
        warning(
            "Comment not found",
            user_id=g.user.id,
            comment_id=comment_id,
            channel_id=channel.id,
        )
        return jsonify({"error": "Comment not found."}), 404

    try:
        # Get user's credentials
        from .services import decrypt_data

        access_token = decrypt_data(g.user.access_token_encrypted)

        # Check if access token exists
        if not access_token:
            error("No access token found", user_id=g.user.id)
            return (
                jsonify(
                    {"error": "Authentication token not found. Please log in again."}
                ),
                401,
            )

        # Create credentials object
        from google.oauth2.credentials import Credentials

        credentials = Credentials(
            token=access_token,
            refresh_token=(
                decrypt_data(g.user.refresh_token_encrypted)
                if g.user.refresh_token_encrypted
                else None
            ),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=current_app.config.get("GOOGLE_CLIENT_ID"),
            client_secret=current_app.config.get("GOOGLE_CLIENT_SECRET"),
        )

        # Create YouTube service and reply to comment
        yt_service = YouTubeService(credentials=credentials)
        response = yt_service.reply_to_comment(comment.youtube_comment_id, reply_text)

        info(
            "Successfully replied to comment",
            user_id=g.user.id,
            comment_id=comment_id,
            youtube_comment_id=comment.youtube_comment_id,
            reply_id=response.get("id"),
        )

        return (
            jsonify(
                {
                    "message": "Reply sent successfully",
                    "reply_id": response.get("id"),
                    "reply_text": reply_text,
                }
            ),
            201,
        )

    except Exception as e:
        error(
            "Failed to reply to comment",
            user_id=g.user.id,
            comment_id=comment_id,
            youtube_comment_id=comment.youtube_comment_id,
            error=str(e),
        )

        # Provide more specific error messages
        error_message = "Failed to send reply"
        error_str = str(e).lower()

        if "quota" in error_str:
            error_message = "YouTube API quota exceeded. Please try again later."
        elif "unauthorized" in error_str or "forbidden" in error_str:
            error_message = "Not authorized to reply to this comment. Please check your permissions."
        elif "not found" in error_str:
            error_message = "Comment not found on YouTube. It may have been deleted."
        elif "invalid" in error_str and "token" in error_str:
            error_message = "Authentication token expired. Please log in again."
        else:
            error_message = f"Failed to send reply: {str(e)}"

        return jsonify({"error": error_message}), 500
