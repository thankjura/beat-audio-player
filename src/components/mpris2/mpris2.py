from gi.repository import GLib

from beat.components.mpris2.dbus import DBusInterface
from beat.components.queue_manager import QueueState
from beat.utils.art_info import ArtInfo


MEDIA_PLAYER2_IFACE = 'org.mpris.MediaPlayer2'
MEDIA_PLAYER2_PLAYER_IFACE = 'org.mpris.MediaPlayer2.Player'
MEDIA_PLAYER2_TRACKLIST_IFACE = 'org.mpris.MediaPlayer2.TrackList'
MEDIA_PLAYER2_PLAYLISTS_IFACE = 'org.mpris.MediaPlayer2.Playlists'


xml_resource = "resource:///ru/slie/beat/mpris2.xml"


class MPRIS2(DBusInterface):
    def __init__(self, app):
        super().__init__(app.props.application_id, xml_resource)
        self.__app = app
        self.__queue = self.__app.props.queue
        self.__player = self.__queue.props.player
        self.__queue.connect("song-changed", self.__on_song_changed)
        self.__queue.connect("notify::state", self.__on_state_changed)

    def __on_state_changed(self, queue, _state):
        playback_status = self.__get_playback_status()
        self.properties_changed(
            MEDIA_PLAYER2_PLAYER_IFACE,
            {'PlaybackStatus': GLib.Variant('s', playback_status), }, [])

    def __on_song_changed(self, queue):
        properties = {}
        properties["Metadata"] = GLib.Variant("a{sv}", self.__get_metadata())
        properties["CanGoNext"] = GLib.Variant("b", self.__queue.has_next)
        properties["CanGoPrevious"] = GLib.Variant("b", self.__queue.has_prev)
        properties["CanPause"] = GLib.Variant("b", True)
        properties["CanPlay"] = GLib.Variant("b", True)

        self.properties_changed(MEDIA_PLAYER2_PLAYER_IFACE, properties, [])

    def __get_playback_status(self):
        state = self.__queue.props.state
        if state == QueueState.STOPPED:
            return 'Stopped'
        elif state == QueueState.PAUSED:
            return 'Paused'
        else:
            return 'Playing'

    def __get_song_dbus_path(self, ref=None):
        if not ref or not ref.valid():
            return "/org/mpris/MediaPlayer2/TrackList/NoTrack"

        store = ref.get_model().uuid
        index = ref.get_path().get_indices()[0]

        return f"/ru/slie/beat/tracklist/{strore}_{index}"

    def __get_metadata(self):
        ref = self.__queue.active_ref
        song_dbus_path = self.__get_song_dbus_path()

        if not ref or not ref.valid():
            return {
                'mpris:trackid': GLib.Variant('o', song_dbus_path)
            }

        model = ref.get_model()

        length = self.__player.props.duration * 1e6
        artist = model.get_artist_for_ref(ref)
        album = model.get_album_for_ref(ref)
        title = model.get_title_for_ref(ref)
        track_path = model.get_track_path_for_ref(ref)

        metadata = {
            'mpris:trackid': GLib.Variant('o', song_dbus_path),
            'xesam:url': GLib.Variant('s', model.get_artist_for_ref(ref)),
            'mpris:length': GLib.Variant('x', length),
            'xesam:album': GLib.Variant('s', album),
            'xesam:title': GLib.Variant('s', title),
            'xesam:artist': GLib.Variant('as', [artist]),
            'xesam:albumArtist': GLib.Variant('as', [artist])
        }

        image_path = ArtInfo(track_path).get_image_path()
        if image_path:
            metadata['mpris:artUrl'] = GLib.Variant('s', "file://" + image_path)

        return metadata

    def get_all(self, interface_name):
        if interface_name == MEDIA_PLAYER2_IFACE:
            application_id = self.__app.props.application_id
            return {
                'CanQuit': GLib.Variant('b', True),
                'Fullscreen': GLib.Variant('b', False),
                'CanRaise': GLib.Variant('b', True),
                'HasTrackList': GLib.Variant('b', True),
                'Identity': GLib.Variant('s', 'Music'),
                'DesktopEntry': GLib.Variant('s', application_id),
                'SupportedUriSchemes': GLib.Variant('as', [
                    'file'
                ]),
                'SupportedMimeTypes': GLib.Variant('as', [
                    'application/ogg',
                    'audio/x-vorbis+ogg',
                    'audio/x-flac',
                    'audio/mpeg'
                ]),
            }
        elif interface_name == MEDIA_PLAYER2_PLAYER_IFACE:
            position_msecond = int(self.__player.position * 1e6)
            playback_status = self.__get_playback_status()
            # TODO: can play
            can_play = True
            has_previous = self.__queue.has_prev
            return {
                'PlaybackStatus': GLib.Variant('s', playback_status),
                'Metadata': GLib.Variant('a{sv}', self.__get_metadata()),
                'Position': GLib.Variant('x', position_msecond),
                'CanGoNext': GLib.Variant('b', self.__queue.has_next),
                'CanGoPrevious': GLib.Variant('b', has_previous),
                'CanPlay': GLib.Variant('b', can_play),
                'CanPause': GLib.Variant('b', can_play),
                'CanSeek': GLib.Variant('b', True),
                'CanControl': GLib.Variant('b', True),
            }
        elif interface_name == MPRIS.MEDIA_PLAYER2_TRACKLIST_IFACE:
            return {
                'Tracks': GLib.Variant('ao', self._path_list),
                'CanEditTracks': GLib.Variant('b', False)
            }
        elif interface_name == MPRIS.MEDIA_PLAYER2_PLAYLISTS_IFACE:
            playlist_count = self._playlists_model.get_n_items()
            active_playlist = self._get_active_playlist()
            return {
                'PlaylistCount': GLib.Variant('u', playlist_count),
                'Orderings': GLib.Variant('as', ['Alphabetical']),
                'ActivePlaylist': GLib.Variant('(b(oss))', active_playlist),
            }
        elif interface_name == 'org.freedesktop.DBus.Properties':
            return {}
        elif interface_name == 'org.freedesktop.DBus.Introspectable':
            return {}
        else:
            self._log.warning(
                "MPRIS does not implement {} interface".format(interface_name))

    def get(self, interface_name, property_name):
        try:
            return self.__get_all(interface_name)[property_name]
        except KeyError:
            msg = "MPRIS does not handle {} property from {} interface".format(
                property_name, interface_name)
            print(msg)
            raise ValueError(msg)

    def set(self, interface_name, property_name, new_value):
        if interface_name == MEDIA_PLAYER2_IFACE:
            if property_name == 'Fullscreen':
                pass
        elif interface_name == MEDIA_PLAYER2_PLAYER_IFACE:
            if property_name in ['Rate', 'Volume']:
                pass
        else:
            print(f"MPRIS does not implement {interface_name} interface")

    def properties_changed(self, interface_name, changed_properties,
                                 invalidated_properties):
        parameters = {
            'interface_name': interface_name,
            'changed_properties': changed_properties,
            'invalidated_properties': invalidated_properties
        }
        self.dbus_emit_signal('PropertiesChanged', parameters)

    def _raise(self):
        self.__app.up()

    def quit(self):
        self.__app.quit()

    def next(self):
        self.__queue.play_next()

    def previous(self):
        self.__queue.play_prev()

    def pause(self):
        self.__queue.pause()

    def play_pause(self):
        self.__queue.play()

    def stop(self):
        self.__queue.stop()

    def play(self):
        self.__queue.play()
