import os
from datetime import datetime, timedelta

import requests
from requests_oauthlib import OAuth2Session
from sqlalchemy.dialects.postgresql import JSONB

from gifsync.config import REFRESH_URL
from gifsync.extensions import db
from gifsync.models.songs import Song
from gifsync.util import spotify_request


class SpotifyUser(db.Model):  # type: ignore[name-defined]
    __tablename__ = "spotify_user"

    id = db.Column(db.String(32), primary_key=True)
    access_token = db.Column(db.String(256), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)
    refresh_token = db.Column(db.String(256), nullable=False)
    preferences = db.Column(JSONB, nullable=True)
    curr_song: dict | None = None

    @staticmethod
    def get_user_id(access_token):
        response, content = spotify_request("me", access_token)
        if response.status_code == 200 and "id" in content:
            return content["id"]
        return None

    def __init__(self, access_token, expiration_time, refresh_token, id_=None):
        if not id_:
            self.id = SpotifyUser.get_user_id(  # pylint: disable=invalid-name
                access_token
            )
        else:
            self.id = id_
        self.access_token = access_token
        self.expiration_time = expiration_time
        self.refresh_token = refresh_token

    def update_curr_song(self):
        if self.expiration_time < datetime.utcnow():
            self.refresh_access_token()
        response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer " + self.access_token,
            },
            timeout=60,
        )
        self.curr_song = {}
        if response.status_code == 200:
            content = response.json()
            # When an ad is playing for users w/out premium,
            # content['item'] = None, so we must check first
            # Additionally, when user is playing a local file,
            # state that we are paused
            if content.get("item") and not content["item"].get("is_local"):
                self.curr_song["name"] = content["item"]["name"]
                self.curr_song["id"] = content["item"]["id"]
                self.curr_song["tempo"] = self.clamp_tempo(
                    Song.get_song_tempo(self.curr_song["id"], self.access_token)
                )
                track_duration = int(content["item"]["duration_ms"])
                track_progress = int(content["progress_ms"])
                self.curr_song["remaining_ms"] = track_duration - track_progress
                self.curr_song["artists"] = []
                for artist in content["item"]["artists"]:
                    self.curr_song["artists"].append(artist["name"])
            else:
                self.curr_song["paused"] = "true"
        elif response.status_code == 204:
            self.curr_song["paused"] = "true"
        return self.curr_song

    def clamp_tempo(self, tempo: float) -> float:
        clamped_tempo = tempo
        if self.preferences is not None:
            if clamped_tempo <= self.preferences.get("min_tempo", 0):
                clamped_tempo *= 2
            elif clamped_tempo >= self.preferences.get("max_tempo", 999):
                clamped_tempo /= 2
        return clamped_tempo

    def refresh_access_token(self):
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        refresh_token = {"refresh_token": self.refresh_token}
        extra = {"client_id": client_id, "client_secret": client_secret}
        spotify_oauth = OAuth2Session(client_id, token=refresh_token)
        token = spotify_oauth.refresh_token(REFRESH_URL, **extra)
        self.access_token = token["access_token"]
        expires_in = float(token["expires_in"])
        self.expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
        if "refresh_token" in token:
            self.refresh_token = token["refresh_token"]
        db.session.commit()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id


class AnonymousUser:
    @property
    def is_authenticated(self):
        return False

    @property
    def is_active(self):
        return False

    @property
    def is_anonymous(self):
        return True

    def get_id(self):
        return
