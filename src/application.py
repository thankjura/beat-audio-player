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

import sys
import gi

from gi.repository import Gtk, Gio, GObject, GLib
from gettext import gettext as _

from .window import BeatWindow
from .player import Player
from .settings import Settings


__all__ = ["Application"]


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='ru.slie.beat',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        self.__window = None
        self.__player = Player(self)

        self.connect("command-line", self.__on_command_line)
        # command line
        self.add_main_option("append", ord("a"), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, _("Append to current playlist instead of create new"), None)

    def __on_command_line(self, _app, command_line):
        options = command_line.get_options_dict()
        self.activate()

        files = command_line.get_arguments()[1:]
        if files:
            playlist = None
            if options.contains("append"):
                playlist = self.__window.props.playlist
            if not playlist:
                playlist = self.__window.create_playlist_tab(_("new playlist"), selected=True)

            for f in files:
                playlist.add_tracks(f)

            if not options.contains("append"):
                playlist.play()

        return 0

    @GObject.Property(type=Player, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def player(self):
        return self.__player

    @GObject.Property(type=BeatWindow, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def win(self):
        return self.__window

    def do_activate(self):
        if not self.__window:
            self.__window = BeatWindow(self)
            Settings(self)
            if not self.__window.props.playlist:
                self.__window.create_playlist_tab(_("new playlist"))
        self.__window.present()

