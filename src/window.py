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

from gi.repository import Gtk, GObject
from .widgets.header import HeaderBar
from .widgets.progress import ProgressBar
from .widgets.playlist import PlayList


@Gtk.Template(resource_path='/ru/slie/beat/ui/window.ui')
class BeatWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'BeatWindow'

    __body = Gtk.Template.Child("_body")
    __notebook = Gtk.Template.Child("_notebook")

    PLAYLISTS = []

    def __init__(self, app, **kwargs):
        super().__init__(application=app, **kwargs)

        self.__app = app
        self.__header = HeaderBar(self.__app)
        self.__progress = ProgressBar(self.__app)
        self.__playlist = PlayList(self.__app)
        self.set_titlebar(self.__header)

        self.__body.pack_start(self.__progress, False, False, 0)
        self.__body.reorder_child(self.__progress, 0)

        scrollbox = Gtk.ScrolledWindow()
        scrollbox.add_with_viewport(self.__playlist)
        scrollbox.show_all()
        # self.__playlist.show_all()
        self.__notebook.append_page(scrollbox, Gtk.Label(label=self.__playlist.label))

        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/03. Steal This Album!/02 - Innervision.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/03. Steal This Album!/15 - Roulette.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/02. Toxicity/05 - X.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/02. Toxicity/06 - Chop Suey!.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/02. Toxicity/07 - Bounce.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/02. Toxicity/09 - Atwa.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/02. Toxicity/12 - Toxicity.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/02 - B.Y.O.B..flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/04 - Cigaro.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/05 - Radio,Video.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/06 - This Cocaine Makes Me Feel Like I'm On This Song.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/07 - Violent Pornography.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/09 - Sad Statue.flac")
        self.__playlist.add_track("/home/GrandMaster/Music/System Of A Down/04. Mezmerize/10 - Old School Hollywood.flac")

    @GObject.Property(type=PlayList, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def playlist(self):
        return self.__playlist
