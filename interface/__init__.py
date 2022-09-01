from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery


app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'],
                          backend=app.config['CELERY_RESULT_BACKEND'])


from interface import routes

if __name__ == "__main__":
    app.run()
