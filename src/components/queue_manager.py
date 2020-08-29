from enum import IntEnum

from gi.repository import GObject

from beat.components.player import Player, Playback
from beat.components.queue import TracksQueue



class QueueState(IntEnum):
    STOPPED = 0
    PAUSED = 1
    PLAYING = 2


class QueueManager(GObject.GObject):

    __gsignals__ = {
        "song-changed": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__player = Player(self.__app)
        self.__queue = TracksQueue()
        self.__state = QueueState.STOPPED
        self.__player.connect("notify::state", self.__on_player_state)
        self.__player.connect("eos", self.__on_player_eos)
        self.__active_ref = None
        self.__repeat_mode = None
        self.__shuffle = False

    @property
    def repeat_mode(self):
        return self.__repeat_mode

    @repeat_mode.setter
    def repeat_mode(self, mode):
        self.__repeat_mode = mode

    @property
    def shuffle(self):
        return self.__shuffle

    @shuffle.setter
    def shuffle(self, shuffle):
        self.__shuffle = shuffle

    def __on_player_eos(self, player):
        if self.__repeat_mode == "song":
            self.stop()
            self.play()
        else:
            self.play_next()

    def __on_player_state(self, player, _state):
        player_state = player.props.state
        if player_state == Playback.PLAYING:
            self.__state = QueueState.PLAYING
        elif player_state == Playback.PAUSED:
            self.__state = QueueState.PAUSED
        else:
            self.__state = QueueState.STOPPED
        #
        self.notify("state")

    @GObject.Property(type=int, flags=GObject.ParamFlags.READABLE)
    def state(self):
        return self.__state

    @GObject.Property(type=Player, flags=GObject.ParamFlags.READABLE)
    def player(self):
        return self.__player

    def add(self, track_refs):
        self.__queue.add(track_refs)

    def remove(self, track_refs):
        self.__queue.remove(track_refs)

    def stop(self):
        self.__player.stop()

    def play_ref(self, ref):
        self.__active_ref = ref
        self.emit("song-changed")
        track = ref.get_model().get_track_path_for_ref(ref)
        self.__queue.remove(ref)
        self.__player.play(ref.get_model().get_track_path_for_ref(ref))

    def pause(self):
        if self.__player.props.state == Playback.PLAYING:
            self.__player.pause()

    def play(self, ref=None):
        if self.__player.props.state == Playback.PLAYING:
            self.__player.pause()
        elif self.__player.props.state == Playback.PAUSED:
            self.__player.unpause()
        elif self.__queue:
            self.play_ref(self.__queue.next)
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
        if self.__queue:
            self.play_ref(self.__queue.next)
            return

        if self.__player.props.state != Playback.PLAYING:
            return

        if self.__active_ref and self.__active_ref.valid():
            model = self.__active_ref.get_model()
            ref = model.get_next_and_select(shuffle=self.__shuffle)
            if ref:
                self.play_ref(ref)
                return
            elif self.__repeat_mode == "playlist":
                ref = model.get_first_and_select()
                if ref:
                    self.play_ref(ref)
                    return
        self.stop()

    def play_prev(self):
        if self.__player.props.state != Playback.PLAYING:
            return

        if self.__active_ref and self.__active_ref.valid():
            model = self.__active_ref.get_model()
            ref = model.get_prev_and_select()
            if ref:
                self.play_ref(ref)

    @property
    def has_next(self):
        if not self.__active_ref:
            return False

        model = self.__active_ref.get_model()

        return model.get_next_ref(self.__active_ref) != None

    @property
    def has_prev(self):
        if not self.__active_ref:
            return False

        model = self.__active_ref.get_model()

        return model.get_prev_ref(self.__active_ref) != None

    @property
    def active_ref(self):
        return self.__active_ref

    @property
    def active_track_path(self):
        if not self.__active_ref:
            return None

        model = self.__active_ref.get_model()
        return model.get_track_path_for_ref(self.__active_ref)

