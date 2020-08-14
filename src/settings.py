import configparser
import csv
import re
from pathlib import Path
from uuid import uuid4

from gi.repository import GObject, GLib


__all__= ["Settings"]


uuid_regexp = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)


class BeatConfig(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        super().__init__(default_section="main", *args, **kwargs)

    def set_value(self, section, param, value):
        if value is not None:
            value = str(value)
        if not section in self:
            self[section] = {}
        self.set(section, param, value)

    def get_value(self, section, param):
        if not section in self:
            return None
        return self.get(section, param, fallback=None)


class Settings:
    def __init__(self, app):
        self.__app = app
        self.__config_dir = Path(GLib.get_user_config_dir(), "beat")
        self.__config_file = Path(self.__config_dir, "config.ini")
        self.__config = BeatConfig()
        self.__init_dirs()
        self.__load()
        self.__app.props.win.connect("playlist-changed", self.__on_playlist_changed)
        self.__app.props.win.connect("tab-selected", self.__on_playlist_switch)
        self.__app.props.win.connect("tab-renamed", self.__on_playlist_renamed)
        self.__app.props.win.connect("tab-removed", self.__on_playlist_removed)

    def __init_dirs(self):
        if not self.__config_dir.exists():
            self.__config_dir.mkdir(parents=True)

    def __load(self):
        self.__config.read(self.__config_file)

        for p in self.__get_playlists():
            self.__app.props.win.create_playlist_tab(label=p.get("label"),
                                                     rows=p.get("rows"),
                                                     uuid=p.get("uuid"),
                                                     selected=p.get("selected"))

    def __save(self):
        with self.__config_file.open('w') as f:
            self.__config.write(f)

        print("Config saved")

    def __get_playlist_keys(self):
        return [k for k in self.__config if uuid_regexp.match(k)]

    def __get_playlists(self):
        out = []
        need_save = False

        selected_uuid = self.__config.get_value("main", "selected")

        for p in self.__get_playlist_keys():
            filename = self.__config.get_value(p, 'file')
            if not filename:
                self.__config.remove_section(p)
                need_save = True
                continue

            playlist_file = Path(self.__config_dir, filename)
            if not playlist_file.exists():
                self.__config.remove_section(p)
                need_save = True
                continue

            rows = []
            with playlist_file.open() as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)

            out.append({
                "label": self.__config[p].get('label'),
                "rows": rows,
                "uuid": p,
                "position": self.__config[p].get('position'),
                "selected": selected_uuid and selected_uuid == p
            })

            out.sort(key=lambda x: x.get("position"))

        if need_save:
            self.__save()

        return out

    def __on_playlist_changed(self, _win, playlist):
        uuid = playlist.uuid
        if uuid is None:
            return

        filename = self.__config.get_value(uuid, "file")
        if not filename:
            filename = f"{uuid}.csv"
            self.__config.set_value(uuid, "file", filename)
        self.__config.set_value(uuid, "label", playlist.props.label)
        self.__config.set_value(uuid, "position", playlist.props.index)
        self.__save()

        cols = playlist.get_cols()

        with Path(self.__config_dir, filename).open('w') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(cols)
            for row in playlist.get_rows():
                writer.writerow(row)

            print(f"Playlist {playlist.props.label} saved")

    def __on_playlist_switch(self, _win, uuid):
        self.__config.set_value("main", "selected", uuid)
        self.__save()

    def __on_playlist_renamed(self, _win, uuid, label):
        self.__config.set_value(uuid, "label", label)
        self.__save()

    def __on_playlist_removed(self, _win, uuid):
        if not uuid in self.__config:
            return

        filename = self.__config.get_value(uuid, 'file')
        if filename:
            Path(self.__config_dir, filename).unlink(True)

        self.__config.remove_section(uuid)
        self.__save()

