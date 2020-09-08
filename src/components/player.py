from enum import IntEnum
from pathlib import Path
from gi.repository import Gst, GLib, Gtk, GObject


__all__ = ["Player", "Playback"]


class Playback(IntEnum):
    STOPPED = 0
    READY = 1
    PAUSED = 2
    PLAYING = 3


class Player(GObject.GObject):
    __gsignals__ = {
        "clock-tick": (GObject.SignalFlags.RUN_FIRST, None, (int, )),
        "eos": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, app):
        super().__init__()
        Gst.init(None)

        self.__player = Gst.Pipeline.new("player")
        self.__source = Gst.ElementFactory.make("filesrc", "file-source")
        decodebin = Gst.ElementFactory.make('decodebin', 'decodebin')
        audioconvert = Gst.ElementFactory.make('audioconvert', 'audioconvert')

        spectrum = Gst.ElementFactory.make("spectrum", "spectrum")
        spectrum.set_property("bands", 96)
        spectrum.set_property("threshold", -80)
        spectrum.set_property("interval", 10000000)
        spectrum.set_property("post-messages", True)
        spectrum.set_property('message-magnitude', True)

        self.__volume = Gst.ElementFactory.make('volume', 'volume')

        sink = Gst.ElementFactory.make('autoaudiosink', 'autoaudiosink')

        def on_pad_added(_decodebin, pad):
            pad.link(audioconvert.get_static_pad('sink'))

        decodebin.connect('pad-added', on_pad_added)

        [self.__player.add(k) for k in [self.__source, decodebin, audioconvert, spectrum, self.__volume, sink]]
        self.__source.link(decodebin)
        audioconvert.link_filtered(spectrum)
        spectrum.link(self.__volume)
        self.__volume.link(sink)

        self.__bus = self.__player.get_bus()
        self.__bus.add_signal_watch()
        self.__bus.connect('message::error', self.__on_bus_error)
        self.__bus.connect('message::eos', self.__on_bus_eos)
        self.__bus.connect('message::new-clock', self.__on_new_clock)
        self.__bus.connect("message::state-changed", self.__on_state_changed)
        self.__bus.connect("message::stream-start", self.__on_bus_stream_start)

        self.__tick = 0
        self.__state = Playback.STOPPED

    @property
    def playbin(self):
        return self.__player

    def __query_duration(self):
        success, duration = self.__player.query_duration(Gst.Format.TIME)
        if success:
            self.props.duration = duration / Gst.SECOND
        else:
            self.props.duration = duration

    def __on_new_clock(self, bus, message):
        clock = message.parse_new_clock()
        id_ = clock.new_periodic_id(0, 1 * Gst.SECOND)
        clock.id_wait_async(id_, self.__on_clock_tick, None)

    def __on_clock_tick(self, clock, time, id, data):
        self.emit("clock-tick", self.__tick)
        self.__tick += 1

    def __on_bus_stream_start(self, bus, message):
        def delayed_query():
            self.__query_duration()
            self.__tick = 0

        GLib.timeout_add(1, delayed_query)

    def __on_state_changed(self, bus, message):
        if message.src != self.__player:
            return

        old_state, new_state, _ = message.parse_state_changed()

        if new_state == Gst.State.PAUSED:
            self.__state = Playback.PAUSED
        elif new_state == Gst.State.PLAYING:
            self.__state = Playback.PLAYING
        elif new_state == Gst.State.READY:
            self.__state = Playback.READY
        else:
            self.__state = Playback.STOPPED

        self.notify("state")

    def __on_bus_error(self, bus, message):
        error, debug = message.parse_error()
        if error.matches(Gst.CoreError.quark(), Gst.CoreError.MISSING_PLUGIN):
            self.props.state = Playback.STOPPED

        return True

    def __on_bus_eos(self, bus, message):
        self.emit('eos')

    @GObject.Property(type=int, flags=GObject.ParamFlags.READWRITE)
    def state(self):
        return self.__state

    @state.setter
    def state(self, state):
        if state == Playback.PAUSED:
            self.__player.set_state(Gst.State.PAUSED)
        if state == Playback.STOPPED:
            self.__player.set_state(Gst.State.NULL)
        if state == Playback.READY:
            self.__player.set_state(Gst.State.READY)
        if state == Playback.PLAYING:
            self.__player.set_state(Gst.State.PLAYING)
        self.__state = state

    @GObject.Property
    def position(self):
        return self.__player.query_position(Gst.Format.TIME)[1] / Gst.SECOND

    @GObject.Property(type=float)
    def duration(self):
        if self.props.state == Playback.STOPPED:
            return -1
        return self.__duration

    @duration.setter
    def duration(self, duration):
        self.__duration = duration

    def set_position_by_percent(self, progress) -> bool:
        status_duration, duration = self.__player.query_duration(Gst.Format.TIME)
        if status_duration:
            self.__player.seek_simple(Gst.Format.TIME,
                                      Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                      duration / 100 * progress)

    def unpause(self):
        if self.props.state == Playback.PAUSED:
            self.props.state = Playback.PLAYING

    def play(self, filepath: str) -> bool:
        if filepath and Path(filepath).exists():
            if self.__source.get_property("location") != filepath:
                self.props.state = Playback.STOPPED
                self.__source.set_property("location", filepath)
            self.props.state = Playback.PLAYING
            return True

        else:
            self.props.state = Playback.STOPPED
            return False

    def pause(self):
        self.props.state = Playback.PAUSED

    def stop(self):
        self.props.state = Playback.STOPPED

    def set_volume(self, volume: float):
        self.__volume.set_property('volume', volume)

    @property
    def track_path(self):
        return self.__source.get_property("location")
