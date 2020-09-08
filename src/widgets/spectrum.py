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


class SpectrumCol:
    #BRICK_BORDER_SIZE = 1
    #BRICK_BORDER_COLOR = (1.0, 1.0, 1.0, 1.0)

    COLOR_LOWER = (0.0, 0.8, 0.0, 1.0)
    COLOR_UPPER = (0.8, 0.0, 0.0, 1.0)
    COLOR_EXTRM = (0.1, 0.0, 0.0, 1.0)

    COUNT = 8
    GAP = 1


    COLOURS = _interpolate_colors(COLOR_LOWER,
                                  COLOR_UPPER,
                                  COUNT)

    def __init__(self, magnitute, spect_min, spect_max):
        self.__min = spect_min
        self.__max = spect_max
        self.__cur = magnitute

    def update(self, magnitute, spect_min, spect_max):
        self.__min = spect_min
        self.__max = spect_max
        self.__cur = magnitute

    def draw(self, col_width, col_height, cr, x_pos):
        brick_h = (col_height - (self.GAP * (self.COUNT - 1))) / self.COUNT
        if self.__max == self.__min:
            return

        upper = (self.__cur - self.__min)/(self.__max - self.__min) * self.COUNT

        for i in range(self.COUNT):
            if i >= upper:
                break
            y_pos = col_height - i*(brick_h + self.GAP) - brick_h
            cr.rectangle(x_pos, y_pos, col_width, brick_h)
            cr.set_source_rgba(*self.COLOURS[i])
            cr.fill()


class Spectrum(Gtk.DrawingArea):
    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__player = self.__app.props.queue.props.player
        self.__surface = None
        self.__cols_gap = 2
        self.__height_scale = 1.0
        self.__spect_cols = []
        bus = self.__player.playbin.get_bus()
        bus.connect('message', self.__on_message_handler)
        self.__player.connect('notify::state', self.__on_player_state)
        self.__player.connect('eos', self.__on_player_eos)
        self.connect("draw", self.__draw_spectrum)
        # TODO: make change spectrum vis
        #self.connect("button_press_event", self.__on_key_press)
        #self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        # props
        self.props.hexpand = True

    #def __on_key_press(self, _widget, _event):
    #    print("clicked")

    def __on_player_eos(self, player):
        self.__spect_cols = []
        self.queue_draw()

    def __on_player_state(self, player, state):
        if player.props.state != Playback.PLAYING:
            self.__spect_cols = []
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
                magnitude_list = s.get_value("magnitude")[:]
                spect = [i * self.__height_scale for i in magnitude_list]
                GLib.idle_add(self.__delayed_idle_spectrum_update, spect)

        return True

    def __delayed_idle_spectrum_update(self, spect):
        spect_max = max(spect)
        spect_min = min(spect)

        if len(self.__spect_cols) != len(spect):
            self.__spect_cols = []
            for s in spect:
                col = SpectrumCol(s, spect_min, spect_max)
                self.__spect_cols.append(col)
        else:
            for i, s in enumerate(spect):
                col = self.__spect_cols[i]
                col.update(s, spect_min, spect_max)

        self.queue_draw()
        return False

    def __draw_spectrum(self, area, cr):
        if not self.__spect_cols:
            cr.push_group()
            cr.pop_group_to_source()
            cr.paint()
            return True

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cr.push_group()

        cols_count = len(self.__spect_cols)

        col_width = (w - (self.__cols_gap * (cols_count - 1))) / cols_count

        x_pos = 0

        for i, col in enumerate(self.__spect_cols):
            if i != 0:
                x_pos += self.__cols_gap + col_width
            col.draw(col_width, h, cr, x_pos)

        cr.pop_group_to_source()
        cr.paint()

        return True
