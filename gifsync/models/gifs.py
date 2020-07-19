from ..extensions import db
import hashlib


class Gif(db.Model):
    __tablename__ = 'gif'
    __table_args__ = (db.CheckConstraint('beats_per_loop > 0'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('spotify_user.id', ondelete='CASCADE'), nullable=False)
    image_id = db.Column(db.ForeignKey('image.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    beats_per_loop = db.Column(db.Integer, nullable=False)

    image = db.relationship('Image', primaryjoin='Gif.image_id == Image.id',
                            backref=db.backref('gifs', passive_deletes=True))
    user = db.relationship('SpotifyUser', primaryjoin='Gif.user_id == SpotifyUser.id',
                           backref=db.backref('gifs', passive_deletes=True))

    def __init__(self, user_id, image_id, name, beats_per_loop):
        self.user_id = user_id
        self.image_id = image_id
        self.name = name
        self.beats_per_loop = beats_per_loop


class Image(db.Model):
    __tablename__ = 'image'

    id = db.Column(db.String(64), primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)

    def __init__(self, image, id_=None):
        self.image = image
        if not id_:
            image_hash = Image.hash_image(image)
            self.id = image_hash
        else:
            self.id = id_

    @staticmethod
    def hash_image(image):
        return hashlib.sha256(image).hexdigest()
