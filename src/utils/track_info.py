import re
from pathlib import Path
from gettext import gettext as _

from beat.tinytag import TinyTag


__all__ = ["TrackInfo"]


class TrackInfo:
    def __init__(self, url, image=False):
        self.__url = url
        self.__tag = TinyTag.get(url, image=image)
        keywords = ["album", "cover", self.album.lower(), self.artist.lower()]
        self.__cover_pattern = re.compile(".*(" + "|".join(keywords) + ").*\.(jpg|jpeg|png)")

    def is_valid(self):
        return self.__tag is not None

    @property
    def album(self):
        value = self.__tag.album
        if not value:
            return _("unknown album")
        return value

    @property
    def artist(self):
        value = self.__tag.artist
        if not value:
            return _("unknown artist")
        return value

    @property
    def title(self):
        value = self.__tag.title
        if not value:
            return _("unknown")
        return value

    @property
    def duration(self):
        return self.__tag.duration

    @property
    def duration_str(self):
        return self.get_time_str(self.__tag.duration)

    def get_image(self):
        image_data = self.__tag.get_image()
        if image_data:
            return image_data
        else:
            filepath = None
            for f in Path(self.__url).parent.iterdir():
                if f.is_dir():
                    continue

                if self.__cover_pattern.match(f.name.lower()):
                    filepath = f
                    break

            if filepath:
                return filepath.read_bytes()



    @staticmethod
    def get_time_str(seconds) -> str:
        if seconds is None:
            return ""

        sign = False
        if seconds < 0:
            sign = True
            seconds = abs(seconds)
        amount, seconds = divmod(int(seconds), 60)
        return f"{amount}:{seconds:02d}"
