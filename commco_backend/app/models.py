from .extensions import db
from sqlalchemy.orm import relationship


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    access_token_encrypted = db.Column(db.LargeBinary, nullable=False)
    refresh_token_encrypted = db.Column(db.LargeBinary, nullable=True)

    channels = relationship(
        "Channel", back_populates="user", cascade="all, delete-orphan"
    )


class Channel(db.Model):
    __tablename__ = "channels"
    id = db.Column(db.Integer, primary_key=True)
    youtube_channel_id = db.Column(db.String(255), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="channels")
    comments = relationship(
        "Comment", back_populates="channel", cascade="all, delete-orphan"
    )


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    youtube_comment_id = db.Column(db.String(255), unique=True, nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"), nullable=False)

    text_original = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(255))
    author_avatar_url = db.Column(db.String(1024))
    video_id = db.Column(db.String(255))
    published_at = db.Column(db.DateTime(timezone=True))

    # The AI's classification for the MVP
    category = db.Column(
        db.String(50), index=True, nullable=False, default="Miscellaneous"
    )

    channel = relationship("Channel", back_populates="comments")
