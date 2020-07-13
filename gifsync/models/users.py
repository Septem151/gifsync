from ..extensions import db


class SpotifyUser(db.Model):
    __tablename__ = 'spotify_user'

    id = db.Column(db.String(32), primary_key=True)
    access_token = db.Column(db.String(256), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)
    refresh_token = db.Column(db.String(256), nullable=False)

    def __init__(self, id_, access_token, expiration_time, refresh_token):
        self.id = id_
        self.access_token = access_token
        self.expiration_time = expiration_time
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
