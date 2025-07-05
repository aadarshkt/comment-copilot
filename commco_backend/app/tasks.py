from flask import current_app
from .models import db, User, Channel, Comment
from .services import YouTubeService, decrypt_data, GeminiService, encrypt_data
from datetime import datetime
from dateutil.parser import isoparse
import google.oauth2.credentials
import google.auth.transport.requests
from .extensions import celery


@celery.task(name="app.process_channel_comments")
def process_channel_comments(channel_id):
    channel = Channel.query.get(channel_id)
    if not channel:
        return "Channel not found."

    user = channel.user

    # 1. Decrypt tokens to get credentials
    decrypted_access_token = decrypt_data(user.access_token_encrypted)
    decrypted_refresh_token = decrypt_data(user.refresh_token_encrypted)

    creds = google.oauth2.credentials.Credentials(
        token=decrypted_access_token,
        refresh_token=decrypted_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=celery.conf.get("GOOGLE_CLIENT_ID"),
        client_secret=celery.conf.get("GOOGLE_CLIENT_SECRET"),
    )

    # 2. Refresh token if needed
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(google.auth.transport.requests.Request())
            # Update stored tokens with refreshed ones
            user.access_token_encrypted = encrypt_data(creds.token)
            if creds.refresh_token:
                user.refresh_token_encrypted = encrypt_data(creds.refresh_token)
            db.session.commit()
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            return f"Token refresh failed: {e}"

    # 2. Initialize Services
    yt_service = YouTubeService(credentials=creds)
    ai_service = GeminiService()

    # 3. Fetch latest comments from YouTube
    try:
        comments_from_api = yt_service.get_latest_comments(channel.youtube_channel_id)
    except Exception as e:
        if "insufficientPermissions" in str(e) or "403" in str(e):
            return f"Permission denied: User may not have access to comments on channel {channel.youtube_channel_id}. Error: {e}"
        else:
            return f"Failed to fetch comments: {e}"

    # 4. Process and save/update comments
    new_comment_count = 0
    updated_comment_count = 0
    for item in comments_from_api:
        top_level_comment = item["snippet"]["topLevelComment"]["snippet"]
        comment_id_yt = item["snippet"]["topLevelComment"]["id"]

        # Check if comment already exists
        existing_comment = (
            db.session.query(Comment)
            .filter_by(youtube_comment_id=comment_id_yt)
            .first()
        )

        # Classify with AI
        category = ai_service.classify_comment(top_level_comment["textOriginal"])

        if existing_comment:
            # Update existing comment's category
            if existing_comment.category != category:
                existing_comment.category = category
                updated_comment_count += 1
        else:
            # Create new comment object
            new_comment = Comment(
                youtube_comment_id=comment_id_yt,
                channel_id=channel.id,
                text_original=top_level_comment["textOriginal"],
                author_name=top_level_comment["authorDisplayName"],
                author_avatar_url=top_level_comment["authorProfileImageUrl"],
                video_id=top_level_comment["videoId"],
                published_at=isoparse(top_level_comment["publishedAt"]),
                category=category,
            )
            db.session.add(new_comment)
            new_comment_count += 1

    if new_comment_count > 0 or updated_comment_count > 0:
        db.session.commit()

    return f"Processed {len(comments_from_api)} comments. Added {new_comment_count} new comments, updated {updated_comment_count} existing comments."
