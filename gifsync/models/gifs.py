from ..config import gif_frames_path
from ..extensions import db
import hashlib
from io import BytesIO
import math
import os
from pathlib import Path
from PIL import Image as PilImage


class Gif(db.Model):
    __tablename__ = 'gif'
    __table_args__ = (db.CheckConstraint('beats_per_loop > 0'),)

    id = db.Column(db.String(16), primary_key=True)
    user_id = db.Column(db.ForeignKey('spotify_user.id', ondelete='CASCADE'), nullable=False)
    image_id = db.Column(db.ForeignKey('image.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = db.Column(db.String(256), nullable=False)
    beats_per_loop = db.Column(db.Integer, nullable=False)

    image = db.relationship('Image', primaryjoin='Gif.image_id == Image.id',
                            backref=db.backref('gifs', passive_deletes=True))
    user = db.relationship('SpotifyUser', primaryjoin='Gif.user_id == SpotifyUser.id',
                           backref=db.backref('gifs', passive_deletes=True))

    def __init__(self, user_id, image_id, name, beats_per_loop, id_=None):
        self.user_id = user_id
        self.image_id = image_id
        self.name = name
        self.beats_per_loop = beats_per_loop
        if not id_:
            self.id = Gif.generate_hash_id(user_id, name)
        else:
            self.id = id_

    @staticmethod
    def generate_hash_id(user_id, name):
        return hashlib.sha256(f'{user_id}{name}'.encode('utf-8')).hexdigest()[:16]

    @staticmethod
    def round_tens(num):
        a = (num // 10) * 10
        b = a + 10
        return int(b if num - a >= b - num else a)

    @staticmethod
    def get_frame_times(num_frames, tempo, beats_per_loop):
        # Calculate the number of seconds per beat in order to get number of milliseconds per loop
        beats_per_sec = tempo / 60
        secs_per_beat = 1 / beats_per_sec
        duration = Gif.round_tens(secs_per_beat * beats_per_loop * 1000)
        frame_times = []
        # Try to make frame times as even as possible by dividing duration by number of frames
        actual_duration = 0
        for _ in range(0, num_frames):
            frame_time = Gif.round_tens(duration / num_frames)
            frame_times.append(frame_time)
            actual_duration += frame_time
        # Adjust frame times to match as closely as possible to the actual duration, rounded to multiple of 10
        # Keep track of which indexes we've added to already and attempt to split corrections as evenly as possible
        # throughout the frame times
        correction = duration - actual_duration
        adjust_val = int(math.copysign(10, correction))
        i = 0
        seen_i = {i}
        while actual_duration != duration:
            frame_times[i % num_frames] += adjust_val
            actual_duration += adjust_val
            if i not in seen_i:
                seen_i.add(i)
            elif len(seen_i) == num_frames:
                seen_i.clear()
                i = 0
            else:
                i += 1
            i += num_frames // abs(correction // 10)
        return frame_times

    def get_synced_gif(self, tempo):
        original_frames = self.image.get_frames()
        frame_times = Gif.get_frame_times(len(original_frames), tempo, self.beats_per_loop)
        synced_frames = []
        for i in range(0, len(original_frames)):
            path_to_frame = os.path.join(gif_frames_path, f'{self.image.id}/{i}.png')
            pil_image = PilImage.open(path_to_frame)
            # Convert the image into P mode but only use 255 colors in the palette out of 256
            alpha = pil_image.getchannel('A')
            pil_image = pil_image.convert('RGB').convert('P', palette=PilImage.ADAPTIVE, colors=255)
            # Set all pixel values below 128 to 255 , and the rest to 0
            mask = PilImage.eval(alpha, lambda a: 255 if a <= 128 else 0)
            # Paste the color of index 255 and use alpha as a mask
            pil_image.paste(255, mask)
            # The transparency index is 255
            pil_image.info['transparency'] = 255
            synced_frames.append(pil_image)
        synced_image = BytesIO()
        synced_frames[0].save(
            synced_image,
            format='GIF',
            save_all=True,
            append_images=synced_frames[1:],
            loop=0,
            duration=frame_times,
            disposal=2
        )
        return synced_image


class Image(db.Model):
    __tablename__ = 'image'

    id = db.Column(db.String(16), primary_key=True)
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
        return hashlib.sha256(image).hexdigest()[:16]

    def analyse_image(self):
        # Pre-process pass over the image to determine the mode (full or additive).
        # Necessary as assessing single frames isn't reliable. Need to know the mode
        # before processing all frames.
        pil_image = PilImage.open(BytesIO(self.image))
        results = {
            'size': pil_image.size,
            'mode': 'full',
        }
        try:
            while True:
                if pil_image.tile:
                    tile = pil_image.tile[0]
                    update_region = tile[1]
                    update_region_dimensions = update_region[2:]
                    if update_region_dimensions != pil_image.size:
                        results['mode'] = 'partial'
                        break
                pil_image.seek(pil_image.tell() + 1)
        except EOFError:
            pass
        return results

    def save_frames(self):
        Path(f'{gif_frames_path}/{self.id}').mkdir(parents=True, exist_ok=True)
        mode = self.analyse_image()['mode']
        pil_image = PilImage.open(BytesIO(self.image))
        num_frames = 0
        p = pil_image.getpalette()
        last_frame = pil_image.convert('RGBA')
        try:
            while True:
                # If the GIF uses local colour tables, each frame will have its own palette.
                # If not, we need to apply the global palette to the new frame.
                if not pil_image.getpalette():
                    pil_image.putpalette(p)
                new_frame = PilImage.new('RGBA', pil_image.size)
                # Is this file a "partial"-mode GIF where frames update a region
                # of a different size to the entire image?
                # If so, we need to construct the new frame by pasting it on top of the preceding frames.
                if mode == 'partial':
                    new_frame.paste(last_frame)
                new_frame.paste(pil_image, (0, 0), pil_image.convert('RGBA'))
                new_frame.save(os.path.join(gif_frames_path, f'{self.id}/{num_frames}.png'), 'PNG')
                num_frames += 1
                last_frame = new_frame
                pil_image.seek(pil_image.tell() + 1)
        except EOFError:
            pass

    def get_frames(self):
        path_to_frames = os.path.join(gif_frames_path, str(self.id))
        if not os.path.exists(path_to_frames):
            self.save_frames()
        frame_files = os.listdir(path_to_frames)
        return frame_files
