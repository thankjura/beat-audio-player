from gi.repository import Gtk


@Gtk.Template(resource_path="/ru/slie/beat/ui/footer.ui")
class StatusBar(Gtk.Statusbar):
    __gtype_name__ = "StatusBar"

    def __init__(self, app):
        self.__app = app
        self.__app.props.player.connect("notify::state", self.__on_player_state)

    def __on_player_state(self, player, state):
        pass
