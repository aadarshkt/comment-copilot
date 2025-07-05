from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from celery import Celery


# Extension instances (to be initialized with app in factory)
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

celery = Celery(
    __name__,
    include=["app.tasks"],
)
