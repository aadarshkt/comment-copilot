from flask import Flask
from .extensions import db, migrate, cors
from . import routes, models
from config import Config
from .extensions import celery
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # CORS Configuration - Allow multiple origins
    allowed_origins = [
        "http://localhost:3000",  # React default port
        "http://localhost:8080",  # Current frontend port
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:8080",  # Alternative localhost
    ]

    # Add production origins if specified in environment
    if os.getenv("FRONTEND_URL"):
        allowed_origins.append(os.getenv("FRONTEND_URL"))

    # Add any additional origins from environment variable
    additional_origins = os.getenv("ADDITIONAL_CORS_ORIGINS", "").split(",")
    allowed_origins.extend(
        [origin.strip() for origin in additional_origins if origin.strip()]
    )

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
    )

    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        broker_connection_retry_on_startup=True,  # Ensures retry on startup for Celery 6+
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                # Tasks can now use `current_app`, `g`, database connections, etc.
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    app.app_context().push()

    # Register blueprints
    app.register_blueprint(routes.main_bp)

    return app
