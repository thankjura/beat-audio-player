from gi.repository import Gtk, GdkPixbuf


__all__ = ['CellRendererActiveTrack', 'CellRendererDuration']


class CellRendererActiveTrack(Gtk.CellRendererPixbuf):
    __ACTIVE_PB = GdkPixbuf.Pixbuf.new_from_resource_at_scale("/ru/slie/beat/icons/active.svg", 16, 16, True)
    __PAUSE_PB = GdkPixbuf.Pixbuf.new_from_resource_at_scale("/ru/slie/beat/icons/pause.svg", 16, 16, True)
    __PLAY_PB = GdkPixbuf.Pixbuf.new_from_resource_at_scale("/ru/slie/beat/icons/play.svg", 16, 16, True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_state(self, state):
        if state == "stop":
            self.set_property("pixbuf", self.__ACTIVE_PB)
        elif state == "pause":
            self.set_property("pixbuf", self.__PAUSE_PB)
        elif state == "play":
            self.set_property("pixbuf", self.__PLAY_PB)
        else:
            self.set_property("pixbuf", None)


# TODO: convert seconds to text
class CellRendererDuration(Gtk.CellRendererText):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    
