from collections import namedtuple

import cairo
from gi.repository import Gst, Gtk, Gdk, GObject, GLib

from beat.components.player import Playback


def _interpolate_colors(start_color, target_color, steps):
    out = [start_color]

    if steps < 2:
        return out


    if steps > 2:
        step_deltas = []

        for pair in zip(start_color, target_color):
            delta = (pair[1] - pair[0]) / (steps - 1)
            step_deltas.append(delta)

        for s in range(0, steps - 2):
            out.append([c + step_deltas[i] for i, c in enumerate(out[-1])])

    out.append(target_color)

    return out

class Spectrum(Gtk.DrawingArea):
    LINE_SIZE = 1
    LINE_COLOR = (1.0, 0.0, 0.0, 1.0)
    LINE_GHOST_SIZE = 1
    LINE_GHOST_COLOR_S = (0.8, 0.0, 0.0, 0.8)
    LINE_GHOST_COLOR_E = (0.8, 0.8, 0.2, 0.1)
    LINE_GHOST_NUM = 5

    LINE_GHOST_COLOURS = _interpolate_colors(LINE_GHOST_COLOR_E,
                                             LINE_GHOST_COLOR_S,
                                             LINE_GHOST_NUM)

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__player = self.__app.props.queue.props.player
        self.__surface = None
        self.__height_scale = 1.0
        self.__spect_data = []
        bus = self.__player.playbin.get_bus()
        bus.connect('message', self.__on_message_handler)
        self.__player.connect('notify::state', self.__on_player_state)
        self.__player.connect('eos', self.__on_player_eos)
        self.connect("draw", self.__draw_spectrum)

        # props
        self.props.hexpand = True

    def __on_player_eos(self, player):
        self.__spect_data = []
        self.queue_draw()

    def __on_player_state(self, player, state):
        if player.props.state != Playback.PLAYING:
            self.__spect_data = []
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
        if len(self.__spect_data) > self.LINE_GHOST_NUM:
            self.__spect_data = self.__spect_data[-self.LINE_GHOST_NUM:]

        self.__spect_data.append(spect)
        self.queue_draw()
        return False

    def __draw_spectrum(self, area, cr):
        if not self.__spect_data:
            cr.push_group()
            cr.pop_group_to_source()
            cr.paint()
            return True

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cr.push_group()
        # cr.set_line_join(cairo.LineJoin.ROUND)
        # cr.set_line_cap(cairo.LineCap.ROUND)

        length = len(self.__spect_data)
        for i, data in enumerate(self.__spect_data):
            if i == length - 1:
                line_size = self.LINE_SIZE
                cr.set_line_width(line_size)
                cr.set_source_rgba(*self.LINE_COLOR)
            else:
                line_size = self.LINE_GHOST_SIZE
                cr.set_line_width(line_size)
                cr.set_source_rgba(*self.LINE_GHOST_COLOURS[i-1])

            min_m = min(data)
            max_m = max(data)
            if min_m == max_m:
                continue

            b_width = w / (len(data) + 1)

            cr.move_to(w, h)
            next_w = w
            for b in data:
                next_h = h - ((b - min_m)/(max_m - min_m) * h) + line_size
                next_w -= b_width
                cr.line_to(next_w, next_h)

            cr.line_to(0, h + line_size)
            cr.stroke()

        cr.pop_group_to_source()
        cr.paint()

        return True
