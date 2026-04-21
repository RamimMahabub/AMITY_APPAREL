import os
from pathlib import Path

from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

RENDER_SQLITE_PATH = Path('/opt/render/project/src/instance/amity_apparel.db')


def default_database_uri():
    configured_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
    if configured_uri:
        return configured_uri

    sqlite_path = RENDER_SQLITE_PATH if os.environ.get('RENDER') == 'true' else basedir / 'instance' / 'amity_apparel.db'
    return f"sqlite:///{sqlite_path.as_posix()}"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key'
    SQLALCHEMY_DATABASE_URI = default_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(basedir / 'app' / 'static' / 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit for uploads
