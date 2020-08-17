from gi.repository import Gtk, GLib

from beat.utils.track_info import TrackInfo
from beat.player import Playback


__all__ = ["ProgressBar"]


@Gtk.Template(resource_path="/ru/slie/beat/ui/progress.ui")
class ProgressBar(Gtk.Box):
    __gtype_name__ = "ProgressBar"

    __current_position_label = Gtk.Template.Child("_current_position")
    __duration_label = Gtk.Template.Child("_duration")
    __progress_bar = Gtk.Template.Child("_progress_bar")

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__current_position_label.set_text("00:00")
        self.__duration_label.set_text("00:00")
        self.__player = self.__app.queue.props.player
        self.__player.connect("clock-tick", self.__on_player_clock_tick)
        self.__player.connect("notify::state", self.__on_player_state)
        self.__progress_handler_id = self.__progress_bar.connect("change-value", self.__on_seek)
        # TODO: block handler
        # self.__progress_bar.connect("button-press-event", self.__on_start_seeking)
        self.__progress_bar.connect("button-release-event", self.__on_finish_seeking)
        self.__progress_seeking_position = None

    def __on_finish_seeking(self, _btn, _event):
        if self.__progress_seeking_position != None:
            self.__player.set_position_by_percent(self.__progress_seeking_position)

    def __on_seek(self, progress, scroll, value):
        self.__progress_seeking_position = value

    def __on_player_state(self, player, *args):
        def delayed_query():
            duration = player.props.duration
            if duration is not None and duration > 0:
                self.__duration_label.set_text(TrackInfo.get_time_str(duration))
            else:
                self.__duration_label.set_text(TrackInfo.get_time_str(0))

        GLib.timeout_add(1, delayed_query)

        if player.props.state in (Playback.STOPPED, Playback.READY):
            self.__set_progress(0)

    def __set_progress(self, percent):
            self.__progress_bar.handler_block(self.__progress_handler_id)
            self.__progress_bar.set_value(percent)
            self.__progress_bar.handler_unblock(self.__progress_handler_id)

    def __on_player_clock_tick(self, player, val):
        duration = player.props.duration
        current = player.props.position
        if not duration:
            self.__current_position_label.set_text(TrackInfo.get_time_str(0))
            return
        if duration > 0.0 and current >= 0.0:
            self.__set_progress(current / duration * 100)
            self.__current_position_label.set_text(TrackInfo.get_time_str(current))
        else:
            self.__current_position_label.set_text(TrackInfo.get_time_str(0))

