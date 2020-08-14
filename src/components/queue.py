from gi.repository import GObject

from beat.components.player import Player, Playback


class PlayerQueue(GObject.GObject):

    __gsignals__ = {
        "state": (GObject.SignalFlags.RUN_FIRST, None, (str, ))
    }

    def __init__(self, app):
        self.__app = app
        self.__active_playlist = None
        self.__player = Player(self.__app)

    @GObject.Property(type=Player, flags=GObject.ParamFlags.READABLE)
    def player(self):
        return self.__player

    def stop(self):
        self.__player.stop()

    def playlist_play(self, playlist, track):
        self.__active_playlist = playlist
        self.__player.play(track)

    def play(self):
        if self.__player.props.state == Playback.PLAYING:
            self.__player.pause()
        elif self.__player.props.state == Playback.PAUSED:
            self.__player.unpause()
        else:
            self.__active_playlist = self.__app.props.win.props.playlist
            if not self.__active_playlist:
                return
            tracks = self.__active_playlist.get_selected()
            if tracks:
                self.__player.play(tracks[0])
            else:
                track = self.__active_playlist.get_first_and_select()
                if track:
                    self.__player.play(track)

    def play_next(self):
        if self.__player.props.state != Playback.PLAYING:
            return

        if self.__active_playlist:
            track = self.__active_playlist.get_next_and_select()
            if track:
                self.__player.play(track)

    def play_prev(self):
        if self.__player.props.state != Playback.PLAYING:
            return

        if self.__active_playlist:
            track = self.__active_playlist.get_prev_and_select()
            if track:
                self.__player.play(track)
