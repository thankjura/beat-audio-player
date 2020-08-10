import configparser
import csv
from pathlib import Path

from gi.repository import GObject, GLib


__all__= ["Settings"]



class Settings:
    def __init__(self, app):
        self.__app = app
        self.__config_dir = Path(GLib.get_user_config_dir(), "beat")
        self.__config_file = Path(self.__config_dir, "config.ini")
        self.__config = configparser.ConfigParser(default_section="main")
        self.__init_dirs()
        self.__load()
        self.__app.props.win.connect("playlist-changed", self.__on_playlist_changed)
        self.__app.props.win.connect("tab-selected", self.__on_playlist_switch)

    def __init_dirs(self):
        if not self.__config_dir.exists():
            self.__config_dir.mkdir(parents=True)

    def __load(self):
        self.__config.read(self.__config_file)

        for p in self.__get_playlists():
            self.__app.props.win.create_playlist_tab(p.get("label"), p.get("rows"), silent=True)

        selected_tab = self.__config["main"].get("playlist")
        if selected_tab is not None:
            self.__app.props.win.select_tab(int(selected_tab), silent=True)

    def __save(self):
        with self.__config_file.open('w') as f:
            self.__config.write(f)

    def __get_playlists(self):
        out = []
        need_save = False
        playlists = sorted([p for p in self.__config.keys() if p.lower().startswith("playlist")])
        for p in playlists:
            filename = self.__config[p].get('file')
            if not filename:
                del self.__config[p]
                need_save = True
                continue

            playlist_file = Path(self.__config_dir, filename)
            if not playlist_file.exists():
                del self.__config[p]
                need_save = True
                continue

            rows = []
            with playlist_file.open() as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            out.append({
                "label": self.__config[p].get('label'),
                "rows": rows
            })

        if need_save:
            self.save()

        return out

    def __on_playlist_changed(self, win, playlist):
        index = playlist.props.index
        if index is None:
            return

        filename = f"playlist_{index:03d}.csv"
        self.__config[f"Playlist {index}"] = {
            "label": playlist.props.label,
            "file": filename
        }
        self.__save()

        cols = playlist.get_cols()

        with Path(self.__config_dir, filename).open('w') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(cols.keys())
            for row in playlist.get_rows():
                writer.writerow(row)

    def __on_playlist_switch(self, win, index):
        self.__config["main"]["playlist"] = str(index)
        self.__save()

    def get_playlist_index(self):
        return None
