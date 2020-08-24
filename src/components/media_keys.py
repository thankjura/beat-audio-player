from gi.repository import GObject, Gio, GLib, Gtk

__all__ = ['MediaKeys']


class MediaKeys(GObject.GObject):
    __gtype_name__ = 'MediaKeys'

    def __init__(self, app):
        super().__init__()

        self.__queue = app.props.queue
        self.__window = app.props.win

        self.__media_keys_proxy = None

        self.__init_media_keys_proxy()

    def __init_media_keys_proxy(self):
        def name_appeared(connection, name, name_owner, data=None):
            Gio.DBusProxy.new_for_bus(
                Gio.BusType.SESSION,
                Gio.DBusProxyFlags.DO_NOT_LOAD_PROPERTIES, None,
                "org.gnome.SettingsDaemon.MediaKeys",
                "/org/gnome/SettingsDaemon/MediaKeys",
                "org.gnome.SettingsDaemon.MediaKeys", None,
                self.__media_keys_proxy_ready)

        Gio.bus_watch_name(
            Gio.BusType.SESSION, "org.gnome.SettingsDaemon.MediaKeys",
            Gio.BusNameWatcherFlags.NONE, name_appeared, None)

    def __media_keys_proxy_ready(self, proxy, result, data=None):
        try:
            self.__media_keys_proxy = proxy.new_finish(result)
        except GLib.Error as e:
            print("Error: Failed to contact settings daemon:", e.message)
            return

        self.__media_keys_proxy.connect("g-signal", self.__handle_media_keys)

        ctrlr = Gtk.EventControllerKey().new(self.__window)
        ctrlr.props.propagation_phase = Gtk.PropagationPhase.CAPTURE
        ctrlr.connect("focus-in", self.__grab_media_player_keys)

    def __grab_media_player_keys(self, controllerkey=None):
        def proxy_call_finished(proxy, result, data=None):
            try:
                proxy.call_finish(result)
            except GLib.Error as e:
                print(f"Error: Failed to grab mediaplayer keys: {e.message}")
        self.__media_keys_proxy.call(
            "GrabMediaPlayerKeys", GLib.Variant("(su)", ("Beat", 0)),
            Gio.DBusCallFlags.NONE, -1, None, proxy_call_finished)

    def __handle_media_keys(self, proxy, sender, signal, parameters):
        app, response = parameters.unpack()
        if app != "Beat":
            return

        if "Play" in response:
            self.__queue.play()
        elif "Stop" in response:
            self.__queue.stop()
        elif "Next" in response:
            self.__queue.play_next()
        elif "Previous" in response:
            self.__queue.play_prev()
