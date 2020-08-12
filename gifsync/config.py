import os

# CLIENT_ID and CLIENT_SECRET **MUST** be defined in environment variables
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
flask_env = os.environ.get('FLASK_ENV', 'development')
flask_secret = os.environ.get('SECRET_KEY', 'devkey')
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:devpassword@localhost:5432/postgres')
port = int(os.environ.get('PORT', 8000))
callback_uri = os.environ.get('CALLBACK_URI', f'http://localhost:{port}/callback')
authorization_base_url = 'https://accounts.spotify.com/authorize'
token_url = 'https://accounts.spotify.com/api/token'
refresh_url = token_url
scope = ['user-read-currently-playing']
csp = {
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
gif_frames_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/gif_frames')
synced_gifs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/synced_gifs')
