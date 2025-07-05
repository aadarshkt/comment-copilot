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
    g
)
from .models import db, User, Channel, Comment
from .services import encrypt_data, YouTubeService
from .tasks import process_channel_comments
import google_auth_oauthlib.flow
from google.oauth2 import credentials
import requests

import os
# THIS IS THE FIX:
# This line tells oauthlib that it's okay to use HTTP for local development.
# You MUST NOT use this in production.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Define the Blueprint for our API routes
main_bp = Blueprint('main', __name__, url_prefix='/api')


# --- Decorator for Protecting Routes ---
def login_required(f):
    """
    Ensures a user is logged in before allowing access to a route.
    Also loads the user object into Flask's global 'g' object.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
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

@main_bp.route('/auth/google/login')
def google_login():
    """
    Redirects the user to Google's OAuth consent screen.
    """
    # Note: For production, use a more secure way to handle the client secrets file.
    # For now, we assume 'client_secret.json' is in the root directory.
    if not os.path.exists('client_secret.json'):
        return jsonify({"error": "Google client secret file not found on server."}), 500

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=[
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/youtube.readonly', # Key scope for the MVP
            'openid'
        ],
        redirect_uri=url_for('main.google_callback', _external=True)
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Gets a refresh token
        prompt='consent'        # Ensures user is prompted for permissions
    )
    session['state'] = state
    return redirect(authorization_url)


@main_bp.route('/auth/google/callback')
def google_callback():
    """
    Handles the callback from Google after user grants permissions.
    Creates or updates the user, and establishes a session.
    """
    state = session.get('state')
    if not state or state != request.args.get('state'):
        return jsonify({"error": "State mismatch. Invalid request."}), 400

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=None, # to prevent CSRF
        state=state,
        redirect_uri=url_for('main.google_callback', _external=True)
    )
    
    # 'access_type=offline' is required to get a refresh token.
    # 'prompt=consent' forces the consent screen to appear every time, 
    # ensuring a refresh token is issued (useful in development).
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    # Get user profile information
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        headers={'Authorization': f'Bearer {creds.token}'}
    )
    if not user_info_response.ok:
        return jsonify({"error": "Failed to fetch user info from Google."}), 500
    
    user_info = user_info_response.json()
    google_id = user_info['id']

    # --- Find or Create User in our Database ---
    user = User.query.filter_by(google_id=google_id).first()
    
    encrypted_access_token = encrypt_data(creds.token)
    encrypted_refresh_token = encrypt_data(creds.refresh_token) if creds.refresh_token else None

    if user:
        # User exists, update their tokens
        user.access_token_encrypted = encrypted_access_token
        if encrypted_refresh_token:
            user.refresh_token_encrypted = encrypted_refresh_token
    else:
        # New user: create a new record
        user = User(
            google_id=google_id,
            email=user_info['email'],
            access_token_encrypted=encrypted_access_token,
            refresh_token_encrypted=encrypted_refresh_token
        )
        db.session.add(user)
        db.session.flush() # Flush

    # Also fetch and create their primary YouTube Channel
    if not user.channels or len(user.channels) == 0:
        yt_service = YouTubeService(credentials=creds)
        channels_data = yt_service.get_user_channels()
        if channels_data:
            # For MVP, we just take the first channel_data[0]
            channel_data = channels_data[0]
            new_channel = Channel(
                youtube_channel_id=channel_data['id'],
                user_id=user.id
            )
            db.session.add(new_channel)
    
    db.session.commit()

    # Log the user in by storing their DB id in the session
    session.clear()
    session['user_id'] = user.id

    # Redirect to the frontend dashboard
    return redirect(os.getenv('FRONTEND_URL', 'http://localhost:3000/dashboard/comments'))


@main_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """
    Logs the user out by clearing the session.
    """
    session.clear()
    return jsonify({"message": "Successfully logged out."}), 200


# =================
# USER & APP ROUTES
# =============================================================================

@main_bp.route('/user/me')
@login_required
def get_current_user():
    """
    Returns basic information about the currently logged-in user.
    Useful for the frontend to confirm login status.
    """
    return jsonify({
        "id": g.user.id,
        "email": g.user.email,
        "channel_id": g.user.channels[0].youtube_channel_id if g.user.channels else None
    })

@main_bp.route('/channel/sync', methods=['POST'])
@login_required
def sync_channel():
    """
    Triggers a background job to fetch and classify the latest comments for the user's channel.
    """
    if not g.user.channels:
        return jsonify({"error": "No YouTube channel linked to this account."}), 404
    channel = g.user.channels[0]
    process_channel_comments.delay(channel.id)
    return jsonify({"message": "Channel sync has been started."}), 202

@main_bp.route('/comments')
@login_required
def get_comments():
    """
    Fetches categorized comments from the database for the user's channel.
    Accepts a 'category' query parameter to filter results.
    """
    valid_categories = ["Needs Action", "Quick Acknowledge", "Review & Delete"]
    category_filter = request.args.get('category', 'Needs Action')
    if category_filter not in valid_categories:
        return jsonify({"error": f"Invalid category. Must be one of {valid_categories}"}), 400
    if not g.user.channels:
        return jsonify({"error": "No YouTube channel linked to this account."}), 404
    channel = g.user.channels[0]
    comments = Comment.query.filter_by(
        channel_id=channel.id,
        category=category_filter
    ).order_by(Comment.published_at.desc()).limit(100).all()
    result = [
        {
            "id": c.id,
            "youtube_comment_id": c.youtube_comment_id,
            "text_original": c.text_original,
            "author_name": c.author_name,
            "author_avatar_url": c.author_avatar_url,
            "video_id": c.video_id,
            "published_at": c.published_at.isoformat(),
            "category": c.category
        } for c in comments
    ]
    return jsonify(result)