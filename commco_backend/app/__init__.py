from flask import Flask
from .extensions import db, migrate, cors
from . import routes, models
from config import Config
from .extensions import celery



def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": "http://localhost:8080"}},
        supports_credentials=True,
    )  # Adjust origin for production

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
