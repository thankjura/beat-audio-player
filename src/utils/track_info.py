import re
from hashlib import md5
from pathlib import Path
from gettext import gettext as _

from beat.tinytag import TinyTag



__all__ = ["TrackInfo"]


class TrackInfo:
    def __init__(self, url):
        self.__url = url
        self.__tag = TinyTag.get(url, image=False)

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
