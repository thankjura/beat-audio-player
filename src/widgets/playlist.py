from pathlib import Path
from urllib.parse import unquote
from gi.repository import Gtk, Gdk, GObject
from ..utils.track_info import TrackInfo

COLS = {
        "_src":     str,
        "_current": bool,
        "Artist":   str,
        "Album":    str,
        "Title":    str,
        "Length":   str
}

TARGETS = [
        ('GTK_LIST_BOX_ROW',    Gtk.TargetFlags.SAME_WIDGET, 0),
        ('text/plain',          0, 1),
        ('TEXT',                0, 2),
        ('STRING',              0, 3),
]


ROW_ATOM = Gdk.Atom.intern_static_string("GTK_LIST_BOX_ROW")


class PlayListStore(Gtk.ListStore):
    __gtype_name__ = "PlayListStore"
    def __init__(self):
        super().__init__(*[t for col, t in COLS.items()])



class PlayList(Gtk.TreeView):
    __gtype_name__ = "PlayList"

    label = GObject.Property(type=str, default='bar')

    def __init__(self, app):
        super().__init__()
        self.__app = app
        self.__selection = self.get_selection()
        self.__store = PlayListStore()
        self.__player =self.__app.props.player
        self.set_model(self.__store)

        self.connect("button-press-event", self.__on_button_press)
        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                    TARGETS, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)
        self.enable_model_drag_dest(TARGETS, Gdk.DragAction.DEFAULT)
        self.drag_dest_add_text_targets()
        self.drag_source_add_text_targets()
        self.connect("drag_data_get", self.__on_data_get)
        self.connect("drag_data_received", self.__on_data_drop)
        self.connect("drag_data_delete", self.__on_data_delete)
        for col_index, col in enumerate(COLS.keys()):
            if col.startswith("_"):
                continue
            if COLS[col] == str:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(col, renderer, text=col_index)
                self.append_column(column)
        self.show_all()


    def __on_button_press(self, view, event):
        if event.type != Gdk.EventType.DOUBLE_BUTTON_PRESS:
            return
        track = self.get_selected()
        if track:
            self.__player.play(track)


    @staticmethod
    def __on_data_get(view, context, selection_data, info, timestamp):
        tree_selection = view.get_selection()
        model, paths = tree_selection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        iter_str = ','.join([model.get_string_from_iter(it) for it in iters])
        selection_data.set(ROW_ATOM, 0, iter_str.encode())

    def __on_data_delete(self, view, *args):
        # TODO: delete
        print("delete row")

    def __on_data_drop(self, view, context, x, y, selection_data, info, timestamp):
        store = view.get_model()
        data = selection_data.get_data()

        drop_info = view.get_dest_row_at_pos(x, y)
        if not data:
            return
        position_iter = None
        insert_after = True

        if drop_info:
            path, position = drop_info
            position_iter = store.get_iter(path)

            if position in (Gtk.TreeViewDropPosition.BEFORE,
                            Gtk.TreeViewDropPosition.INTO_OR_BEFORE,
                            Gtk.TreeViewDropPosition.INTO_OR_AFTER):
                insert_after = False
            else:
                insert_after = True

        if selection_data.get_data_type() == ROW_ATOM:
            selected_iters = [store.get_iter(int(x)) for x in data.decode().split(",")]

            if position_iter:
                if position_iter in selected_iters:
                    return
                if insert_after:
                    for i in selected_iters:
                        store.move_after(i, position_iter)
                else:
                    for i in selected_iters:
                        store.move_before(i, position_iter)
            else:
                for i in selected_iters:
                    store.move_before(i, None)
        else:
            paths = data.decode().split("\n")
            for p in paths:
                filepath = unquote(p.strip().replace("file://", "", 1))
                self.add_tracks(filepath, position_iter, insert_after)

    def get_selected(self):
        model, tree_iter = self.__selection.get_selected()
        if tree_iter is not None:
            return model[tree_iter][0]
        else:
            tree_iter = model.get_iter_first()
            if tree_iter is not None:
                self.__selection.select_iter(tree_iter)
                return model[tree_iter][0]

    def get_prev(self):
        model, tree_iter = self.__selection.get_selected()
        if tree_iter is not None:
            prev_iter = model.iter_previous(tree_iter)
            if prev_iter:
                self.__selection.select_iter(prev_iter)
                return model[prev_iter][0]

    def get_next(self):
        model, tree_iter = self.__selection.get_selected()
        if tree_iter is not None:
            next_iter = model.iter_next(tree_iter)
            if next_iter:
                self.__selection.select_iter(next_iter)
                return model[next_iter][0]

    def add_tracks(self, path, position_iter, insert_after):
        path = Path(path)
        if not path.exists():
            return False

        if path.is_file():
            return self.add_track(str(path), position_iter, insert_after)

    def add_track(self, url: str, position_iter=None, insert_after=True) -> bool:
        info = TrackInfo(url)
        if not info.is_valid():
            return False
        row = [url, False, info.get_tag("artist"), info.get_tag("album"), info.get_tag("title"), info.get_len_str()]

        if position_iter:
            if insert_after:
                self.__store.insert_after(position_iter, row)
            else:
                self.__store.insert_before(position_iter, row)
        else:
            self.__store.append(row)

        return True
