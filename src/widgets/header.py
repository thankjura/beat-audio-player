from gi.repository import Gtk
from ..player import Playback


__all__ = ["HeaderBar"]


@Gtk.Template(resource_path="/ru/slie/beat/ui/header.ui")
class HeaderBar(Gtk.HeaderBar):
    __gtype_name__ = "HeaderBar"

    __button_play_img = Gtk.Template.Child("_button_play_img")
    __button_volume = Gtk.Template.Child("_button_volume")

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__player = app.props.player
        self.__player.connect("notify::state", self.__on_player_state)

    def __open_files(self, keep_tab: bool):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a file", parent=self.__app.props.win, action=Gtk.FileChooserAction.OPEN
        )
        dialog.set_select_multiple(True)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:

            playlist = None

            if keep_tab:
                playlist = self.__app.props.win.props.playlist

            if playlist is None:
                playlist = self.__app.props.win.create_playlist_tab("playlist", selected=True)

            for uri in dialog.get_filenames():
                playlist.add_tracks(uri, None, True)
            playlist.emit("changed")

        dialog.destroy()


    @Gtk.Template.Callback()
    def _on_open_files(self, button):
        self.__open_files(False)

    @Gtk.Template.Callback()
    def _on_add_files(self, button):
        self.__open_files(True)

    @Gtk.Template.Callback()
    def _on_stop(self, button):
        self.__player.stop()

    @Gtk.Template.Callback()
    def _on_play(self, button):
        if self.__player.props.state == Playback.PLAYING:
            self.__player.pause()
        else:
            track = self.__app.props.win.props.playlist.get_selected()
            if track:
                self.__player.play(track)

    @Gtk.Template.Callback()
    def _on_prev(self, button):
        if self.__player.props.state != Playback.PLAYING:
            return
        track = self.__app.props.win.props.playlist.get_prev()
        if track:
            self.__player.play(track)

    @Gtk.Template.Callback()
    def _on_next(self, button):
        if self.__player.props.state != Playback.PLAYING:
            return
        track = self.__app.props.win.props.playlist.get_next()
        if track:
            self.__player.play(track)

    @Gtk.Template.Callback()
    def _on_volume_changed(self, _widget, value):
        self.__app.props.player.set_volume(value)

    def __on_player_state(self, player, state):
        player_state = player.props.state
        if player_state == Playback.PLAYING:
            self.__button_play_img.set_from_icon_name("gtk-media-pause",
                                                       Gtk.IconSize.BUTTON)
        else:
            self.__button_play_img.set_from_icon_name("gtk-media-play",
                                                       Gtk.IconSize.BUTTON)
