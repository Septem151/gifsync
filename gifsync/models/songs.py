import requests
from gifsync.extensions import db


class Song(db.Model):
    __tablename__ = "song"

    id = db.Column(db.String(32), primary_key=True)
    tempo = db.Column(db.Float, nullable=False)

    def __init__(self, id_, tempo):
        self.id = id_
        self.tempo = tempo

    @staticmethod
    def get_song_tempo(id_, access_token):
        song = Song.query.filter(Song.id == str(id_)).first()
        if not song:
            response = requests.get(
                f"https://api.spotify.com/v1/audio-features/{id_}",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer " + access_token,
                },
            )
            content = response.json()
            if "tempo" in content:
                song = Song(id_, content["tempo"])
                db.session.add(song)
                db.session.commit()
                return song.tempo
            else:
                return None
        else:
            return song.tempo
