from gi.repository import Gtk, GdkPixbuf


__all__ = ['CellRendererActiveTrack', 'CellRendererDuration']


class CellRendererActiveTrack(Gtk.CellRendererPixbuf):
    # __ACTIVE_PB = GdkPixbuf.Pixbuf.new_from_resource("/ru/slie/beat/icons/active_track.png")
    __ACTIVE_PB = GdkPixbuf.Pixbuf.new_from_resource_at_scale("/ru/slie/beat/icons/active_track.png", 16, 16, True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_active(self, is_active):
        if is_active:
            self.set_property("pixbuf", self.__ACTIVE_PB)
        else:
            self.set_property("pixbuf", None)


# TODO: convert seconds to text
class CellRendererDuration(Gtk.CellRendererText):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    
