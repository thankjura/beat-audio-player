from gi.repository import AppIndicator3, Gtk
from gettext import gettext as _

from ..player import Playback

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

        self.__play_label = _('Play')
        self.__pause_label = _('Pause')

        menu = Gtk.Menu()
        self.__item_play = Gtk.MenuItem(self.__play_label)
        item_next = Gtk.MenuItem(_('Next'))
        item_prev = Gtk.MenuItem(_('Prev'))
        item_quit = Gtk.MenuItem(_('Quit'))
        self.__item_play.connect("activate", self.__play)
        item_next.connect("activate", self.__next)
        item_prev.connect("activate", self.__prev)
        item_quit.connect("activate", self.__quit)
        menu.append(self.__item_play)
        menu.append(item_next)
        menu.append(item_prev)
        menu.append(Gtk.SeparatorMenuItem())
        menu.append(item_quit)
        menu.show_all()
        self.__indicator.set_menu(menu)

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

    def __prev(self, item):
        self.__app.props.queue.play_prev()

    def __quit(self, item):
        self.__app.quit()
