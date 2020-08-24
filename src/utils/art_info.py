import re
import shutil
from hashlib import md5
from pathlib import Path

from gi.repository import GLib

from beat.tinytag import TinyTag


__all__ = ["ArtInfo"]


class ArtInfo:
    def __init__(self, url):
        self.__url = url
        self.__md5 = md5(url.encode()).hexdigest()
        self.__tag = TinyTag.get(url, image=True)
        keywords = ["album", "cover"]
        if self.__tag.album:
            keywords.append(self.__tag.album.lower())
        if self.__tag.artist:
            keywords.append(self.__tag.artist.lower())

        self.__cover_pattern = re.compile(".*(" + "|".join(keywords) + ").*\.(jpg|jpeg|png)")

        self.__cache_dir = Path(GLib.get_user_cache_dir(), "beat", "art")

        if not self.__cache_dir.exists():
            self.__cache_dir.mkdir(parents=True)

    def get_image_path(self):
        path = Path(self.__cache_dir, self.__md5)
        if path.exists():
            return str(path)

        image_data = self.__tag.get_image()
        if image_data:
            with path.open(mode='wb') as f:
                f.write(image_data)

            return str(path)

        else:
            filepath = None
            for f in Path(self.__url).parent.iterdir():
                if f.is_dir():
                    continue

                if self.__cover_pattern.match(f.name.lower()):
                    filepath = f
                    break

            if filepath:
                shutil.copyfile(filepath, str(path))
                return str(path)

