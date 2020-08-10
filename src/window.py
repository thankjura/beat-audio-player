# window.py
#
# Copyright 2020 thankjura
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GObject, Gdk
from gettext import gettext as _

from .widgets.header import HeaderBar
from .widgets.progress import ProgressBar
from .widgets.playlist import PlayList, PLAYLIST_COLS


__all__ = ["BeatWindow"]


class Tab(Gtk.Box):
    __gtype_name__ = 'Tab'

    def __init__(self, label, **kwargs):
        super().__init__(Gtk.Orientation.HORIZONTAL, spacing=10)
        self.__label = Gtk.Label(label=label)
        self.__event_box = Gtk.EventBox()
        self.__menu = Gtk.Menu()
        self.__menu_rename_item = Gtk.MenuItem(_("Rename"))
        self.__menu_delete_item = Gtk.MenuItem(_("Delete"))
        self.__menu.add(self.__menu_rename_item)
        self.__menu.add(self.__menu_delete_item)
        self.__menu.show_all()
        self.__event_box.add(self.__label)

        self.pack_start(self.__event_box, True, True, 0)
        self.__event_box.connect("button-press-event", self.__on_button_press)
        self.show_all()

    def __on_button_press(self, _widget, event):
        if event.type != Gdk.EventType.BUTTON_PRESS:
            return
        if event.get_button().button != 3:
            return
        self.__menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    @property
    def label(self):
        return self.__label


@Gtk.Template(resource_path='/ru/slie/beat/ui/window.ui')
class BeatWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'BeatWindow'

    __body = Gtk.Template.Child("_body")
    __notebook = Gtk.Template.Child("_notebook")

    __gsignals__ = {
        "playlist-changed": (GObject.SignalFlags.RUN_FIRST, None, (PlayList,)),
        "playlist-removed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "tab-selected": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, app, **kwargs):
        super().__init__(application=app, **kwargs)

        self.__app = app
        self.__header = HeaderBar(self.__app)
        self.__progress = ProgressBar(self.__app)
        self.set_titlebar(self.__header)

        self.__body.pack_start(self.__progress, False, False, 0)
        self.__body.reorder_child(self.__progress, 0)
        self.__notebook.connect("switch-page", self.__on_switch_tab)

    def __on_switch_tab(self, _notebook, _page, index):
        self.emit("tab-selected", index)

    def __toggle_show_tabs(self):
        if self.__notebook.get_n_pages() > 1:
            self.__notebook.set_show_tabs(True)
        else:
            self.__notebook.set_show_tabs(False)

    def __on_playlist_chaned(self, playlist):
        self.emit("playlist-changed", playlist)

    def create_playlist_tab(self, label, rows=None, current=False, silent=False) -> PlayList:
        playlist = PlayList(self.__app, label)
        playlist.connect("changed", self.__on_playlist_chaned)
        scrollbox = Gtk.ScrolledWindow()
        scrollbox.add_with_viewport(playlist)
        if rows:
            for row in rows:
                playlist.add_row([row.get(c) for c in PLAYLIST_COLS], silent=silent)

        tab = Tab(label)
        scrollbox.show_all()

        page = self.__notebook.append_page(scrollbox, tab)
        self.__toggle_show_tabs()
        if current:
            self.select_tab(page)
        return playlist

    def __delete_tab(self, index):
        self.__notebook.remove_page(index)
        self.__toggle_show_tabs()

    def __on_tab_close_button_event(self, img, event):
        print(img)
        print(event)

    def select_tab(self, index, silent=False):
        if index is None:
            index = -1

        tabs_count = self.__notebook.get_n_pages()
        if tabs_count < index:
            index = 0

        self.__notebook.set_current_page(index)

        self.emit("tab-selected", index)

    @GObject.Property(type=PlayList, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def playlist(self):
        scrollbox = self.__notebook.get_nth_page(self.__notebook.get_current_page())
        if scrollbox is None:
            return None

        return scrollbox.get_children()[0].get_children()[0]
