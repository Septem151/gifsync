import hashlib
import re
import subprocess
from decimal import ROUND_HALF_UP, Decimal
from http import HTTPStatus

from flask import abort

from gifsync.extensions import db


class Gif(db.Model):  # type: ignore[name-defined]
    __tablename__ = "gif"
    __table_args__ = (db.CheckConstraint("beats_per_loop > 0"),)

    id = db.Column(db.String(16), primary_key=True)
    user_id = db.Column(
        db.ForeignKey("spotify_user.id", ondelete="CASCADE"), nullable=False
    )
    image_id = db.Column(
        db.ForeignKey("image.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name = db.Column(db.String(256), nullable=False)
    beats_per_loop = db.Column(db.Integer, nullable=False)
    custom_tempo = db.Column(db.Numeric(5, 2), nullable=True)

    image = db.relationship(
        "Image",
        primaryjoin="Gif.image_id == Image.id",
        backref=db.backref("gifs", passive_deletes=True),
    )
    user = db.relationship(
        "SpotifyUser",
        primaryjoin="Gif.user_id == SpotifyUser.id",
        backref=db.backref("gifs", passive_deletes=True),
    )

    def __init__(self, user_id, image_id, name, beats_per_loop, id_=None):
        self.user_id = user_id
        self.image_id = image_id
        self.name = name
        self.beats_per_loop = beats_per_loop
        if not id_:
            self.id = self.generate_hash_id()
        else:
            self.id = id_

    def get_image_id(self):
        return self.image_id

    def generate_hash_id(self):
        return hashlib.sha256(
            f"{self.user_id}{self.get_image_id()}{self.name}".encode("utf-8")
        ).hexdigest()[:16]

    @staticmethod
    def round_tens(num):
        a = (num // 10) * 10
        b = a + 10
        return int(b if num - a >= b - num else a)

    @staticmethod
    def get_frame_times(tempo: float, num_frames: int, beats_per_loop: float) -> list:
        beats_per_second = tempo / 60
        seconds_per_beat = 1 / beats_per_second
        total_duration = int(
            Decimal(seconds_per_beat * beats_per_loop * 100).to_integral_value(
                ROUND_HALF_UP
            )
        )
        base_frame_duration, extra_frame_duration = divmod(total_duration, num_frames)
        frame_times = [base_frame_duration] * num_frames
        for i in range(0, extra_frame_duration):
            frame_times[(i * num_frames // extra_frame_duration) % num_frames] += 1
        return frame_times

    def get_synced_gif(self, tempo: float) -> bytes:
        num_frames = self.image.get_num_frames()
        frame_times = Gif.get_frame_times(tempo, num_frames, self.beats_per_loop)
        args = [
            "gifsicle",
            "-o",
            "-",
        ]
        for frame_index, frame_time in enumerate(frame_times):
            args.append(f"-d{frame_time}")
            args.append(f"#{frame_index}")
        try:
            result = subprocess.run(
                args, input=self.image.image, capture_output=True, check=True
            )
            result_data = result.stdout
            return result_data
        except subprocess.CalledProcessError:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

    def update_name(self, new_name):
        self.name = new_name
        self.id = self.generate_hash_id()


class Image(db.Model):  # type: ignore[name-defined]
    __tablename__ = "image"

    id = db.Column(db.String(16), primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)

    def __init__(self, image, id_=None):
        self.image = image
        if not id_:
            image_hash = self.hash_image()
            self.id = image_hash
        else:
            self.id = id_

    def get_num_frames(self):
        try:
            cmd = subprocess.run(
                ["gifsicle", "-I"], input=self.image, capture_output=True, check=True
            )
            cmd_data = cmd.stdout.decode("utf-8")
            res = re.compile(r"(?P<num_frames>\d+) images").search(cmd_data)
            if res:
                return int(res.group("num_frames"))
            return -1
        except subprocess.CalledProcessError:
            abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Internal server error trying to get number of gif frames",
            )

    def hash_image(self):
        return hashlib.sha256(self.image).hexdigest()[:16]
