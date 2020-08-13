import io

from gi.repository import Gtk, GdkPixbuf, GLib
from PIL import Image, ImageColor

from beat.player import Playback
from beat.utils.track_info import TrackInfo


@Gtk.Template(resource_path="/ru/slie/beat/ui/footer.ui")
class StatusBar(Gtk.Box):
    __gtype_name__ = "StatusBar"

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__app.props.player.connect("notify::state", self.__on_player_state)
        self.__cover_image = Gtk.Image()
        self.pack_start(self.__cover_image, False, False, 0)
        self.add(self.__cover_image)
        self.__track_path = None
        self.show_all()

    def __on_player_state(self, player, state):
        if player.props.state != Playback.PLAYING:
            return

        track_path = player.track_path
        if self.__track_path == track_path:
            return

        self.__track_path = track_path
        track_info = TrackInfo(track_path, image=True)
        image_bytes = track_info.get_image()
        if not image_bytes:
            self.__cover_image.props.pixbuf = None
            return

        pil_image = Image.open(io.BytesIO(image_bytes))
        w, h = pil_image.size
        bytes = GLib.Bytes.new(pil_image.tobytes())

        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(bytes,
                                                 GdkPixbuf.Colorspace.RGB,
                                                 False,
                                                 8,
                                                 w,
                                                 h,
                                                 w*3)

        pixbuf = pixbuf.scale_simple(32, 32, GdkPixbuf.InterpType.BILINEAR)
        self.__cover_image.props.pixbuf = pixbuf
            
