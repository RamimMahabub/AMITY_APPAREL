import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

RENDER_SQLITE_PATH = Path('/opt/render/project/src/instance/amity_apparel.db')


def _normalize_database_uri(uri: str) -> str:
    if uri.startswith('mysql://'):
        return uri.replace('mysql://', 'mysql+pymysql://', 1)
    return uri


def default_database_uri():
    configured_uri = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    if configured_uri:
        return _normalize_database_uri(configured_uri)

    mysql_host = os.environ.get('MYSQL_HOST')
    mysql_database = os.environ.get('MYSQL_DATABASE')
    if mysql_host or mysql_database:
        mysql_user = quote_plus(os.environ.get('MYSQL_USER', 'root'))
        mysql_password = quote_plus(os.environ.get('MYSQL_PASSWORD', ''))
        mysql_host = mysql_host or '127.0.0.1'
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        mysql_database = mysql_database or 'amity_apparel'
        credentials = f'{mysql_user}:{mysql_password}@' if mysql_password else f'{mysql_user}@'
        return f'mysql+pymysql://{credentials}{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'

    sqlite_path = RENDER_SQLITE_PATH if os.environ.get('RENDER') == 'true' else basedir / 'instance' / 'amity_apparel.db'
    return f"sqlite:///{sqlite_path.as_posix()}"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-secret-key'
    SQLALCHEMY_DATABASE_URI = default_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(basedir / 'app' / 'static' / 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit for uploads
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_TIME_LIMIT = 60 * 60
