from enum import IntEnum

from gi.repository import GObject

from beat.components.player import Player, Playback


class QueueState(IntEnum):
    STOPPED = 0
    PAUSED = 1
    PLAYING = 2


class PlayerQueue(GObject.GObject):

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__player = Player(self.__app)
        self.__queue = []
        self.__state = QueueState.STOPPED
        self.__player.connect("notify::state", self.__on_player_state)
        self.__active_ref = None

    def __on_player_state(self, player, _state):
        player_state = player.props.state
        if player_state == Playback.PLAYING:
            self.__state = QueueState.PLAYING
        elif player_state == Playback.PAUSED:
            self.__state = QueueState.PAUSED
        else:
            self.__state = QueueState.STOPPED
        self.notify("state")

    @GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
    def state(self):
        return self.__state

    @GObject.Property(type=Player, flags=GObject.ParamFlags.READABLE)
    def player(self):
        return self.__player

    def add(self, track_ref):
        self.__queue.append(track_ref)

    def stop(self):
        self.__player.stop()

    def play_ref(self, ref):
        self.__active_ref = ref
        track = ref.get_model().get_track_path_for_ref(ref)
        self.__player.play(ref.get_model().get_track_path_for_ref(ref))

    def play(self, ref=None):
        if self.__player.props.state == Playback.PLAYING:
            self.__player.pause()
        elif self.__player.props.state == Playback.PAUSED:
            self.__player.unpause()
        else:
            self.__active_playlist = self.__app.props.win.get_current_playlist()
            ref = self.__active_playlist.active_ref
            if ref:
                self.play_ref(ref)
            else:
                ref = self.__active_playlist.get_first_and_select()
                if ref:
                    self.play_ref(ref)

    def play_next(self):
        if self.__player.props.state != Playback.PLAYING:
            return

        if self.__active_ref and self.__active_ref.valid():
            model = self.__active_ref.get_model()
            ref = model.get_next_and_select()
            if ref:
                self.play_ref(ref)

    def play_prev(self):
        if self.__player.props.state != Playback.PLAYING:
            return

        if self.__active_ref and self.__active_ref.valid():
            model = self.__active_ref.get_model()
            ref = model.get_prev_and_select()
            if ref:
                self.play_ref(ref)

    @property
    def active_ref(self):
        return self.__active_ref
