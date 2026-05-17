from celery import Celery
from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    return app

flask_app = create_app()

celery_app = Celery(__name__,
                    broker=flask_app.config['CELERY_BROKER_URL'],
                    backend=flask_app.config['CELERY_RESULT_BACKEND'])

# Use the new-style 'include' setting to list task modules
celery_app.conf.update(
    include=['ai_models.tasks']
)

# A fix for Windows environments. It forces Celery to use a single process for local development.
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
    worker_concurrency=1
)