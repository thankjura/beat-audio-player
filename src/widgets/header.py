from gi.repository import Gtk

from beat.components.player import Playback
from beat.components.queue_manager import QueueState

__all__ = ["HeaderBar"]


REPEAT_ICONS = {
    "playlist": "media-playlist-repeat-symbolic",
    "song": "media-playlist-repeat-song-symbolic",
}


@Gtk.Template(resource_path="/ru/slie/beat/ui/header.ui")
class HeaderBar(Gtk.HeaderBar):
    __gtype_name__ = "HeaderBar"

    __button_play_img = Gtk.Template.Child("_button_play_img")
    __button_volume = Gtk.Template.Child("_button_volume")
    __button_repeat = Gtk.Template.Child("_button_repeat")
    __button_repeat_img = Gtk.Template.Child("_button_repeat_img")
    __button_shuffle = Gtk.Template.Child("_button_shuffle")

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__queue = app.props.queue

        self.__button_repeat_img.set_from_icon_name(REPEAT_ICONS["playlist"],
                                                      Gtk.IconSize.BUTTON)
        self.__button_shuffle.set_active(self.__queue.shuffle)
        self.__queue.connect("notify::state", self.__on_queue_state)
        self.__button_repeat_handler = \
            self.__button_repeat.connect("clicked", self.__on_repeat_toggled)

        self.__button_shuffle.connect("toggled", self.__on_shuffle_toggled)

    @property
    def button_volume(self):
        return self.__button_volume

    def __on_repeat_toggled(self, button):
        self.__button_repeat.handler_block(self.__button_repeat_handler)
        if not self.__queue.repeat_mode:
            self.__queue.repeat_mode = "playlist"
            self.__button_repeat.set_active(True)
            self.__button_repeat_img.set_from_icon_name(REPEAT_ICONS["playlist"],
                                                      Gtk.IconSize.BUTTON)
        elif self.__queue.repeat_mode == "playlist":
            self.__queue.repeat_mode = "song"
            self.__button_repeat.set_active(True)
            self.__button_repeat_img.set_from_icon_name(REPEAT_ICONS["song"],
                                                      Gtk.IconSize.BUTTON)
        else:
            self.__queue.repeat_mode = None
            self.__button_repeat.set_active(False)
            self.__button_repeat_img.set_from_icon_name(REPEAT_ICONS["playlist"],
                                                      Gtk.IconSize.BUTTON)

        self.__button_repeat.handler_unblock(self.__button_repeat_handler)

    def __on_shuffle_toggled(self, button):
        self.__queue.shuffle = button.get_active()
        return True

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
                playlist = self.__app.props.win.get_current_playlist()

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
        self.__queue.stop()

    @Gtk.Template.Callback()
    def _on_play(self, button):
        self.__queue.play()

    @Gtk.Template.Callback()
    def _on_prev(self, button):
        self.__queue.play_prev()

    @Gtk.Template.Callback()
    def _on_next(self, button):
        self.__queue.play_next()

    @Gtk.Template.Callback()
    def _on_volume_changed(self, _widget, value):
        self.__queue.props.player.set_volume(value)

    def __on_queue_state(self, queue, state):
        queue_state = queue.props.state
        if queue_state == QueueState.PLAYING:
           self.__button_play_img.set_from_icon_name("media-playback-pause-symbolic",
                                                      Gtk.IconSize.BUTTON)
        else:
           self.__button_play_img.set_from_icon_name("media-playback-start-symbolic",
                                                      Gtk.IconSize.BUTTON)
