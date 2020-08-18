import io

from gi.repository import Gtk, GdkPixbuf, GLib
from PIL import Image, ImageColor

from beat.components.player import Playback
from beat.utils.track_info import TrackInfo
from beat.widgets.spectrum import Spectrum


@Gtk.Template(resource_path="/ru/slie/beat/ui/footer.ui")
class StatusBar(Gtk.Box):
    __gtype_name__ = "StatusBar"

    __generic_cover = GdkPixbuf.Pixbuf.new_from_resource_at_scale(
        "/ru/slie/beat/icons/album.svg", 32, 32, True
    )

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__app.queue.props.player.connect("notify::state", self.__on_player_state)
        self.__cover_image = Gtk.Image()
        self.__cover_image.props.pixbuf = self.__generic_cover
        self.pack_start(self.__cover_image, False, False, 0)
        self.__track_path = None

        # spectrum
        self.__spectrum = Spectrum(self.__app)
        self.pack_end(self.__spectrum, True, True, 0)
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
            self.__cover_image.props.pixbuf = self.__generic_cover
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
            
