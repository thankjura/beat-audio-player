from mutagen import File

__all__ = ["TrackInfo"]

class TrackInfo:
    def __init__(self, url):
        self.__file = File(url)

    def is_valid(self):
        return self.__file is not None

    def get_tag(self, tag_name) -> str:
        if not self.__file.tags:
            return "unknown"
        value = self.__file.tags.get(tag_name)
        if not value:
            return "unknown"

        if isinstance(value, list):
            return value[0]

        return value

    def get_len_str(self) -> str:
        seconds = self.__file.info.length
        return self.get_time_str(seconds)

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
