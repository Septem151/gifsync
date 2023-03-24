from gifsync.extensions import db
from gifsync.util import spotify_request


class Song(db.Model):  # type: ignore[name-defined] # pylint: disable=too-few-public-methods
    __tablename__ = "song"

    id = db.Column(db.String(32), primary_key=True)
    tempo = db.Column(db.Float, nullable=False)

    def __init__(self, id_, tempo):
        self.id = id_  # pylint: disable=invalid-name
        self.tempo = tempo

    @staticmethod
    def get_song_tempo(id_, access_token):
        song = Song.query.filter(Song.id == str(id_)).first()
        if not song:
            _, content = spotify_request(f"audio-features/{id_}", access_token)
            if "tempo" in content:
                song = Song(id_, content["tempo"])
                db.session.add(song)
                db.session.commit()
                return song.tempo
            return None
        return song.tempo
