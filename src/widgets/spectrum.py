from collections import namedtuple

import cairo
from gi.repository import Gst, Gtk, Gdk, GObject, GLib

from beat.components.player import Playback


class Spectrum(Gtk.DrawingArea):
    LINE_SIZE = 2
    LINE_COLOR = (1, 0, 0)

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__player = self.__app.props.queue.props.player
        self.__surface = None
        self.__height_scale = 1.0
        self.__spect_data = None
        bus = self.__player.playbin.get_bus()
        bus.connect('message', self.__on_message_handler)
        self.__player.connect('notify::state', self.__on_player_state)
        self.__player.connect('eos', self.__on_player_eos)
        self.connect("draw", self.__draw_spectrum)

        # props
        self.props.hexpand = True

    def __on_player_eos(self, player):
        self.__spect_data = None
        self.queue_draw()

    def __on_player_state(self, player, state):
        if player.props.state != Playback.PLAYING:
            self.__spect_data = None
            self.queue_draw()

    def __on_message_handler(self, bus, message):
        if message.type == Gst.MessageType.ELEMENT:
            s = message.get_structure()
            name = s.get_name()

            if name != "spectrum":
                return True

            waittime = 0
            if s.has_field("stream-time") and s.has_field("duration"):
                waittime = s.get_value("stream-time") + s.get_value("duration")

            if waittime:
                fullstr = s.to_string()
                magstr = fullstr[fullstr.find('{') + 1: fullstr.rfind('}') - 1]
                magnitude_list = [float(x) for x in magstr.split(',')]
                spect = [i * self.__height_scale for i in magnitude_list]
                GLib.idle_add(self.__delayed_idle_spectrum_update, spect)

        return True

    def __delayed_idle_spectrum_update(self, spect):
        self.__spect_data = spect
        self.queue_draw()
        return False

    def __draw_spectrum(self, area, cr):
        data = self.__spect_data
        if not data:
            cr.push_group()
            cr.pop_group_to_source()
            cr.paint()
            return True

        min_m = min(data)
        max_m = max(data)
        if min_m == max_m:
            return True

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        b_width = w / (len(data) + 1)

        cr.push_group()

        cr.set_source_rgb(*self.LINE_COLOR)
        cr.set_line_width(self.LINE_SIZE)

        cr.move_to(w, h)
        next_w = w
        for b in data:
            next_h = h - ((b - min_m)/(max_m - min_m) * h) + self.LINE_SIZE
            next_w -= b_width
            cr.line_to(next_w, next_h)

        cr.line_to(0, h + self.LINE_SIZE)

        cr.stroke()

        cr.pop_group_to_source()
        cr.paint()

        return True
