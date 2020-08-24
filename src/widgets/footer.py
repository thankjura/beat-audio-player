import io

from gi.repository import Gtk, GdkPixbuf, GLib

from beat.components.player import Playback
from beat.utils.art_info import ArtInfo
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

        image_path = ArtInfo(track_path).get_image_path()
        if not image_path:
            self.__cover_image.props.pixbuf = self.__generic_cover
            return

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image_path, 32, 32, True)

        self.__cover_image.props.pixbuf = pixbuf
            
