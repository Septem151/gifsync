import os
from datetime import timedelta

import dotenv

dotenv.load_dotenv("web.env")

# CLIENT_ID and CLIENT_SECRET **MUST** be defined in environment variables
client_id = os.environ.get("CLIENT_ID")
client_secret = os.environ.get("CLIENT_SECRET")
flask_debug = os.environ.get("FLASK_DEBUG", "true").lower() in ["true", "1"]
flask_secret = os.environ.get("SECRET_KEY", "devkey")
db_url = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:devpassword@localhost:5432/postgres"
)
db_url = db_url.replace("postgres://", "postgresql://")
port = int(os.environ.get("PORT", 8000))
REMEMBER_COOKIE_DURATION = timedelta(
    days=int(os.environ.get("REMEMBER_COOKIE_DURATION", 30))
)
callback_uri = os.environ.get("CALLBACK_URI", f"http://localhost:{port}/callback")
AUTHORIZATION_BASE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
REFRESH_URL = TOKEN_URL
scope = ["user-read-currently-playing"]
csp = {
    "default-src": [
        "'self'",
        "'unsafe-inline'",
        "stackpath.bootstrapcdn.com",
        "code.jquery.com",
        "cdn.jsdelivr.net",
        "fonts.googleapis.com",
    ],
    "img-src": ["*", "data:"],
    "font-src": "fonts.gstatic.com",
}
gif_frames_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "static/gif_frames"
)
