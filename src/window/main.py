# main.py
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

from .tab import Tab
from ..widgets.header import HeaderBar
from ..widgets.progress import ProgressBar
from ..widgets.playlist import PlayList


__all__ = ["BeatWindow"]


@Gtk.Template(resource_path='/ru/slie/beat/ui/window.ui')
class BeatWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'BeatWindow'

    __body = Gtk.Template.Child("_body")
    __notebook = Gtk.Template.Child("_notebook")

    __gsignals__ = {
        "playlist-changed": (GObject.SignalFlags.RUN_FIRST, None, (PlayList,)),
        "playlist-removed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "tab-selected": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "tab-renamed": (GObject.SignalFlags.RUN_FIRST, None, (str,str)),
        "tab-removed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
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

    def __on_switch_tab(self, _notebook, page, index):
        playlist = page.get_children()[0].get_children()[0]
        self.emit("tab-selected", playlist.uuid)

    def __toggle_show_tabs(self):
        if self.__notebook.get_n_pages() > 1:
            self.__notebook.set_show_tabs(True)
        else:
            self.__notebook.set_show_tabs(False)

    def __on_playlist_chaned(self, playlist):
        self.emit("playlist-changed", playlist)

    def create_playlist_tab(self, label, rows=None, uuid=None, selected=False) -> PlayList:
        playlist = PlayList(self.__app, label, uuid)
        playlist.connect("changed", self.__on_playlist_chaned)
        scrollbox = Gtk.ScrolledWindow()
        scrollbox.add_with_viewport(playlist)
        if rows:
            cols = playlist.get_cols()
            for row in rows:
                playlist.add_row([row.get(c) for c in cols])

        tab = Tab(label)
        tab.connect("deleted", self.__on_delete_tab, playlist)
        tab.connect("renamed", self.__on_rename_tab, playlist)
        scrollbox.show_all()

        page = self.__notebook.append_page(scrollbox, tab)
        self.__toggle_show_tabs()
        if selected:
            self.__notebook.set_current_page(page)
        return playlist

    def __on_rename_tab(self, _tab, label, playlist):
        self.emit("tab-renamed", playlist.uuid, label)

    def __on_delete_tab(self, tab, playlist):
        page = self.__notebook.page_num(playlist.get_parent().get_parent())
        if not page:
            return

        if page == self.__notebook.get_current_page():
            self.__notebook.set_current_page(0)
        self.__notebook.remove_page(page)
        self.__toggle_show_tabs()
        self.emit("tab-removed", playlist.uuid)

    @GObject.Property(type=PlayList, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def playlist(self):
        scrollbox = self.__notebook.get_nth_page(self.__notebook.get_current_page())
        if scrollbox is None:
            return None

        return scrollbox.get_children()[0].get_children()[0]

