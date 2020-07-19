import os

# CLIENT_ID and CLIENT_SECRET **MUST** be defined in environment variables
client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
default_env = 'development'
default_secret = 'devkey'
default_db_url = 'postgresql://postgres:devpassword@localhost:5432/postgres'
port = int(os.environ.get('PORT', 8000))
redirect_uri = f'http://localhost:{port}/callback'
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
