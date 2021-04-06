import os
import dotenv

dotenv.load_dotenv('web.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'devkey')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    CLIENT_ID = os.environ.get('CLIENT_ID')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_SECRET = os.environ.get('SECRET_KEY', 'devkey')

    DB_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:devpassword@localhost:5432/postgres')
    DB_URI = DB_URI.replace('postgres://', 'postgresql://')
    SQLALCHEMY_DATABASE_URI = DB_URI
    PORT = int(os.environ.get('PORT', 8000))
    CALLBACK_URI = os.environ.get('CALLBACK_URI', f'http://localhost:{PORT}/callback')
    BASE_URL = 'https://accounts.spotify.com/authorize'
    REFRESH_URL = TOKEN_URL = 'https://accounts.spotify.com/api/token'
    SCOPE = ['user-read-currently-playing']
    CSP = {
        'default-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'stackpath.bootstrapcdn.com',
            'code.jquery.com',
            'cdn.jsdelivr.net',
            'fonts.googleapis.com'
        ],
        'img-src': [
            '*',
            'data:'
        ],
        'font-src': 'fonts.gstatic.com'
    }
    GIF_FRAMES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/gif_frames')
    DEBUG = True

config = Config()