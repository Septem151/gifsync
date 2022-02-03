import hashlib
import math
import os
import re
import subprocess
from decimal import ROUND_HALF_UP, Decimal
from http import HTTPStatus
from io import BytesIO
from pathlib import Path

from flask import abort
from gifsync.config import gif_frames_path
from gifsync.extensions import db
from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image as PilImage


class Gif(db.Model):
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
        # For some reason, SQLAlchemy makes the Image ID a string of length 64
        # by adding spaces to the end, despite the
        # database and type declarations of Image class/table stating it's a
        # char(16)
        return self.image_id[:16]

    def generate_hash_id(self):
        return hashlib.sha256(
            f"{self.user_id}{self.get_image_id()}{self.name}".encode("utf-8")
        ).hexdigest()[:16]

    @staticmethod
    def round_tens(num):
        a = (num // 10) * 10
        b = a + 10
        return int(b if num - a >= b - num else a)

    # @staticmethod
    # def get_frame_times(num_frames, tempo, beats_per_loop):
    #     # Calculate the number of seconds per beat in order to get number of
    #     # milliseconds per loop
    #     beats_per_sec = tempo / 60
    #     secs_per_beat = 1 / beats_per_sec
    #     duration = Gif.round_tens(secs_per_beat * beats_per_loop * 1000)
    #     frame_times = []
    #     # Try to make frame times as even as possible by dividing duration by
    #     # number of frames
    #     actual_duration = 0
    #     for _ in range(0, num_frames):
    #         frame_time = Gif.round_tens(duration / num_frames)
    #         frame_times.append(frame_time)
    #         actual_duration += frame_time
    #     # Adjust frame times to match as closely as possible to the actual
    #     # duration, rounded to multiple of 10
    #     # Keep track of which indexes we've added to already and attempt to
    #     # split corrections as evenly as possible
    #     # throughout the frame times
    #     correction = duration - actual_duration
    #     adjust_val = int(math.copysign(10, correction))
    #     i = 0
    #     seen_i = {i}
    #     while actual_duration != duration:
    #         frame_times[i % num_frames] += adjust_val
    #         actual_duration += adjust_val
    #         if i not in seen_i:
    #             seen_i.add(i)
    #         elif len(seen_i) == num_frames:
    #             seen_i.clear()
    #             i = 0
    #         else:
    #             i += 1
    #         i += num_frames // abs(correction // 10)
    #     return frame_times

    # def get_synced_gif(self, tempo):
    #     original_frames = self.image.get_frames()
    #     frame_times = Gif.get_frame_times(
    #         len(original_frames), tempo, self.beats_per_loop
    #     )
    #     synced_frames = []
    #     for path_to_frame in original_frames:
    #         pil_image = PilImage.open(str(path_to_frame))
    #         # Convert the image into P mode but only use 255 colors in the
    #         # palette out of 256
    #         alpha = pil_image.getchannel("A")
    #         pil_image = pil_image.convert("RGB").convert(
    #             "P", palette=PilImage.ADAPTIVE, colors=255
    #         )
    #         # Set all pixel values below 128 to 255 , and the rest to 0
    #         mask = PilImage.eval(alpha, lambda a: 255 if a <= 128 else 0)
    #         # Paste the color of index 255 and use alpha as a mask
    #         pil_image.paste(255, mask)
    #         # The transparency index is 255
    #         pil_image.info["transparency"] = 255
    #         synced_frames.append(pil_image)
    #     synced_image = BytesIO()
    #     synced_frames[0].save(
    #         synced_image,
    #         format="GIF",
    #         save_all=True,
    #         append_images=synced_frames[1:],
    #         loop=0,
    #         duration=frame_times,
    #         disposal=2,
    #     )
    #     return synced_image

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
        except subprocess.CalledProcessError as error:
            abort(HTTPStatus.INTERNAL_SERVER_ERROR)

    def update_name(self, new_name):
        self.name = new_name
        self.id = self.generate_hash_id()


class Image(db.Model):
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

    # @property
    # def path_to_frames(self):
    #     return Path(f"{gif_frames_path}/{self.id}")

    # @property
    # def is_saved_as_frames(self):
    #     return (
    #         self.path_to_frames.exists()
    #         and not Path(gif_frames_path).joinpath(f"${self.id}.gif").exists()
    #     )

    def hash_image(self):
        return hashlib.sha256(self.image).hexdigest()[:16]

    # def save_frames(self):
    #     self.path_to_frames.mkdir(parents=True, exist_ok=True)
    #     temp_gif_path = Path(gif_frames_path).joinpath(f"${self.id}.gif")
    #     with open(temp_gif_path, "wb") as temp_gif_file:
    #         temp_gif_file.write(BytesIO(self.image).read())
    #     with VideoFileClip(str(temp_gif_path), has_mask=True, verbose=False) as clip:
    #         clip.write_images_sequence(
    #             str(self.path_to_frames.joinpath("%03d.png")), logger=None
    #         )
    #     os.remove(temp_gif_path)

    # def get_frames(self):
    #     if not self.path_to_frames.exists():
    #         self.save_frames()
    #     frame_files = os.listdir(self.path_to_frames)
    #     if not self.is_saved_as_frames:
    #         abort(409)
    #     for i in range(0, len(frame_files)):
    #         frame_files[i] = self.path_to_frames.joinpath(frame_files[i])
    #     frame_files.sort()
    #     return frame_files
