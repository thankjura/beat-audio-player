from gi.repository import AppIndicator3, Gtk, Gdk
from gettext import gettext as _

from beat.components.player import Playback

__all__ = ["StatusIndicator"]


class StatusIndicator:
    def __init__(self, app):
        self.__app = app
        status = AppIndicator3.IndicatorStatus.ACTIVE
        category = AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        self.__indicator = AppIndicator3.Indicator.new(app.get_application_id(),
                                                       "beat", category)
        self.__indicator.set_status(status)
        self.__app.props.queue.props.player.connect("notify::state", self.__on_player_state)
        # self.__volume = self.__app.props.win.header.button_volume

        self.__play_label = _('Play')
        self.__pause_label = _('Pause')

        menu = Gtk.Menu()
        self.__item_play = Gtk.MenuItem(self.__play_label)
        item_next = Gtk.MenuItem(_('Next'))
        item_prev = Gtk.MenuItem(_('Prev'))
        item_show = Gtk.MenuItem(_('Show'))
        item_quit = Gtk.MenuItem(_('Quit'))
        self.__item_play.connect("activate", self.__play)
        item_next.connect("activate", self.__next)
        item_prev.connect("activate", self.__prev)
        item_show.connect("activate", self.__show)
        item_quit.connect("activate", self.__quit)
        menu.append(self.__item_play)
        menu.append(item_next)
        menu.append(item_prev)
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(item_show)
        menu.append(item_quit)
        menu.show_all()
        self.__indicator.set_menu(menu)
        self.__indicator.set_secondary_activate_target(item_show)
        #self.__indicator.connect("scroll-event", self.__on_scroll)
        self.__app.props.win.connect("delete-event", self.__on_delete_event)

    def __on_player_state(self, player, state):
        player_state = player.props.state
        if player_state == Playback.PLAYING:
            self.__item_play.set_label(self.__pause_label)
        else:
            self.__item_play.set_label(self.__play_label)

    def __play(self, item):
        self.__app.props.queue.play()

    def __next(self, item):
        self.__app.props.queue.play_next()
        print(self.__app.props.active_window.is_visible())

    def __prev(self, item):
        self.__app.props.queue.play_prev()

    def __show(self, menu, *args):
        self.__app.up()

    def __quit(self, item):
        self.__app.quit()

    def __on_delete_event(self, _win, _event):
        self.__app.props.win.hide()
        return True

    # def __on_scroll(self, _widget, steps_count, direction):

    #     if direction in (Gdk.ScrollDirection.UP, Gdk.ScrollDirection.RIGHT):
    #         sign = 1
    #     else:
    #         sign = -1

    #     adjustment = self.__volume.get_adjustment()
    #     min_value = adjustment.props.lower
    #     max_value = adjustment.props.upper
    #     step = (max_value - min_value) / 10.0
    #     print(max_value, min_value, step)
    #     print(sign)
    #     print(steps_count)

    #     current_value = adjustment.props.value

    #     value = current_value + (step * steps_count * sign)
    #     if value < min_value:
    #         value = min_value
    #     elif value > max_value:
    #         value = max_value

    #     print(f"set value {value}")

    #     if current_value != value:
    #         self.__volume.set_value(value)

