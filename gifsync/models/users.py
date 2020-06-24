from ..extensions import db


class SpotifyUser(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(50), unique=True, nullable=False)
    access_token = db.Column(db.String(256), nullable=False)
    refresh_token = db.Column(db.String(256), nullable=False)

    def __init__(self, spotify_id, access_token, refresh_token):
        self.spotify_id = spotify_id
        self.access_token = access_token
        self.refresh_token = refresh_token

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
        return self.spotify_id

    def __repr__(self):
        return f'User ID: {self.spotify_id} | Is Authenticated: {self.is_authenticated} | Is Active: {self.is_active} ' \
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
