"""Flask configuration."""

UPLOAD_FOLDER = "interface/static/projects"
VIEW_UPLOAD_FOLDER = "/static/projects"
ALLOWED_EXTENSIONS = {'pdf'}
SECRET_KEY = '192bkturyfd22ab9ewa43d1234bawes36c78afcb9a393ec15f71987wa3w4y764727823bca'

SQLALCHEMY_DATABASE_URI = 'sqlite:///pdf_tools.db?check_same_thread=False'

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
