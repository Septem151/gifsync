from ..config import refresh_url
from ..extensions import db
from datetime import datetime, timedelta
from .songs import Song
import os
import requests
from requests_oauthlib import OAuth2Session


class SpotifyUser(db.Model):
    __tablename__ = 'spotify_user'

    id = db.Column(db.String(32), primary_key=True)
    access_token = db.Column(db.String(256), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)
    refresh_token = db.Column(db.String(256), nullable=False)
    curr_song = None

    @staticmethod
    def get_user_id(access_token):
        response = requests.get(
            'https://api.spotify.com/v1/me',
            headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + access_token
            }
        )
        content = response.json()
        if response.status_code == 200 and 'id' in content:
            return content['id']
        else:
            return None

    def __init__(self, access_token, expiration_time, refresh_token, id_=None):
        if not id_:
            self.id = SpotifyUser.get_user_id(access_token)
        else:
            self.id = id_
        self.access_token = access_token
        self.expiration_time = expiration_time
        self.refresh_token = refresh_token

    def update_curr_song(self):
        if self.expiration_time < datetime.utcnow():
            self.refresh_access_token()
        response = requests.get(
            'https://api.spotify.com/v1/me/player/currently-playing',
            headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + self.access_token
            }
        )
        self.curr_song = {}
        if response.status_code == 200:
            content = response.json()
            # Don't trust spotify to respect 204 vs 200
            # When an ad is playing for users w/out premium, content = None, so we must check first
            if not content:
                self.curr_song['paused'] = 'true'
            elif 'item' in content and 'name' in content['item']:
                self.curr_song['name'] = content['item']['name']
                self.curr_song['id'] = content['item']['id']
                self.curr_song['tempo'] = Song.get_song_tempo(self.curr_song['id'], self.access_token)
                track_duration = int(content['item']['duration_ms'])
                track_progress = int(content['progress_ms'])
                self.curr_song['remaining_ms'] = track_duration - track_progress
                self.curr_song['artists'] = []
                for artist in content['item']['artists']:
                    self.curr_song['artists'].append(artist['name'])
        elif response.status_code == 204:
            self.curr_song['paused'] = 'true'
        return self.curr_song

    def refresh_access_token(self):
        client_id = os.environ.get('CLIENT_ID')
        client_secret = os.environ.get('CLIENT_SECRET')
        refresh_token = {'refresh_token': self.refresh_token}
        extra = {
            'client_id': client_id,
            'client_secret': client_secret
        }
        spotify_oauth = OAuth2Session(client_id, token=refresh_token)
        token = spotify_oauth.refresh_token(refresh_url, **extra)
        self.access_token = token['access_token']
        expires_in = float(token['expires_in'])
        self.expiration_time = datetime.utcnow() + timedelta(seconds=expires_in)
        if 'refresh_token' in token:
            self.refresh_token = token['refresh_token']
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

    def __repr__(self):
        return f'User ID: {self.get_id()} | Is Authenticated: {self.is_authenticated} | Is Active: {self.is_active} ' \
               f'| Is Anonymous: {self.is_anonymous}'


class AnonymousUser(object):
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

    def __repr__(self):
        return f'User ID: Anonymous | Is Authenticated: {self.is_authenticated} | Is Active: {self.is_active} ' \
               f'| Is Anonymous: {self.is_anonymous}'
