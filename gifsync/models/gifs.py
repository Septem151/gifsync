from ..extensions import db


class Frame(db.Model):
    __tablename__ = 'frame'

    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)

    def __init__(self, image):
        self.image = image


class Gif(db.Model):
    __tablename__ = 'gif'
    __table_args__ = (db.CheckConstraint('beats_per_loop > 0'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('spotify_user.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    beats_per_loop = db.Column(db.Integer, nullable=False)

    user = db.relationship('SpotifyUser', primaryjoin='Gif.user_id == SpotifyUser.id',
                           backref=db.backref('gifs', passive_deletes=True))

    def __init__(self, user_id, name, beats_per_loop):
        self.user_id = user_id
        self.name = name
        self.beats_per_loop = beats_per_loop


class GifFrame(db.Model):
    __tablename__ = 'gif_frame'
    __table_args__ = (db.CheckConstraint('frame_number >= 0'),)

    gif_id = db.Column(db.ForeignKey('gif.id', ondelete='CASCADE', onupdate='CASCADE'),
                       primary_key=True, nullable=False)
    frame_id = db.Column(db.ForeignKey('frame.id', ondelete='CASCADE', onupdate='CASCADE'),
                         primary_key=True, nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)

    frame = db.relationship('Frame', primaryjoin='GifFrame.frame_id == Frame.id',
                            backref=db.backref('gif_frames', passive_deletes=True))
    gif = db.relationship('Gif', primaryjoin='GifFrame.gif_id == Gif.id',
                          backref=db.backref('gif_frames', passive_deletes=True))

    def __init__(self, gif_id, frame_id, frame_number):
        self.gif_id = gif_id
        self.frame_id = frame_id
        self.frame_number = frame_number
