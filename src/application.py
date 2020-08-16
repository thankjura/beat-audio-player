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

from beat.window import BeatWindow
from beat.settings import Settings
from beat.components.queue import PlayerQueue
from beat.components.indicator import StatusIndicator


__all__ = ["Application"]


class Application(Gtk.Application):
    def __init__(self, app_id):
        super().__init__(application_id=app_id,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        self.__window = None
        self.__queue = PlayerQueue(self)

        self.connect("command-line", self.__on_command_line)
        # command line
        self.add_main_option("append", ord("a"), GLib.OptionFlags.NONE,
                    GLib.OptionArg.NONE,
                    _("Append to current playlist instead of create new"),
                    None)

    def __on_command_line(self, _app, command_line):
        options = command_line.get_options_dict()
        self.activate()

        files = command_line.get_arguments()[1:]
        if not files:
            return 0

        playlist = self.__window.get_current_playlist()

        is_append = options.contains("append")

        if not playlist or (not is_append and playlist.is_saved()):
            playlist = self.__window.create_playlist_tab(_("new playlist"), selected=True)

        added_track_refs = []

        for f in files:
            added_track_refs.extend(playlist.add_tracks(f))

        if not options.contains("append") and added_track_refs:
            self.__queue.play_ref(added_track_refs[0])

        return 0

    @GObject.Property(type=PlayerQueue, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def queue(self):
        return self.__queue

    @GObject.Property(type=BeatWindow, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def win(self):
        return self.__window

    def do_activate(self):
        if not self.__window:
            self.__window = BeatWindow(self)
            Settings(self)
            try:
                StatusIndicator(self)
            except ImportError:
                print("Appincicator3 not found")
            if not self.__window.get_current_playlist():
                self.__window.create_playlist_tab(_("new playlist"))
        self.__window.present()

