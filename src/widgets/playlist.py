from pathlib import Path
from urllib.parse import unquote

from gettext import gettext as _
from gi.repository import Gtk, Gdk, GObject
from uuid import uuid4

from .cell_renderers import CellRendererActiveTrack
from ..utils.track_info import TrackInfo

__all__ = ["PlayList"]

TARGETS = [
        ('GTK_LIST_BOX_ROW',    Gtk.TargetFlags.SAME_WIDGET, 0)
]

ROW_ATOM = Gdk.Atom.intern_static_string("GTK_LIST_BOX_ROW")


PLAYLIST_COLS = [
    {"key": "src",      "label": "",           "type": str,  "cell_type": None},
    {"key": "active",   "label": "",           "type": bool, "cell_type": CellRendererActiveTrack},
    {"key": "artist",   "label": _("Artist"),  "type": str,  "cell_type": Gtk.CellRendererText},
    {"key": "album",    "label": _("Album"),   "type": str,  "cell_type": Gtk.CellRendererText},
    {"key": "title",    "label": _("Title"),   "type": str,  "cell_type": Gtk.CellRendererText},
    {"key": "length",   "label": _("Length"),  "type": str,  "cell_type": Gtk.CellRendererText},
]


class PlayListStore(Gtk.ListStore):
    __gtype_name__ = "PlayListStore"
    def __init__(self):
        super().__init__(*[col["type"] for col in PLAYLIST_COLS])


class PlayList(Gtk.TreeView):
    __gtype_name__ = "PlayList"


    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ())
    }


    def __init__(self, app, label, uuid=None):
        super().__init__()
        self.__app = app
        self.__label = label
        self.__uuid = uuid if uuid else str(uuid4())
        self.__selection = self.get_selection()
        self.__active_iter = None

        # property
        # self.props.enable_search = True
        self.__selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        # store
        self.__store = PlayListStore()
        self.__store.connect("row-changed", self.__save_playlist)
        self.__store_delete_handler_id = self.__store.connect(
                                    "row-deleted", self.__save_playlist)
        self.__store.connect("rows-reordered", self.__save_playlist)

        self.__player = self.__app.props.player

        self.props.activate_on_single_click = False
        self.set_model(self.__store)

        # right click menu
        self.__menu = Gtk.Menu()
        menu_delete_item = Gtk.MenuItem(_("Delete"))
        menu_delete_item.connect("activate", self.__on_row_delete)
        self.__menu.add(menu_delete_item)
        self.__menu.show_all()

        # enable dnd
        self.connect("row-activated", self.__on_row_activated)
        self.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK,
                    TARGETS, Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE)
        self.enable_model_drag_dest(TARGETS, Gdk.DragAction.DEFAULT)
        self.drag_dest_add_text_targets()
        self.drag_source_add_text_targets()

        # make cols
        for col_index, col in enumerate(PLAYLIST_COLS):
            if not col.get("cell_type"):
                continue


            renderer = col.get("cell_type")()
            if col.get("cell_type") == Gtk.CellRendererText:
                column = Gtk.TreeViewColumn(col["label"], renderer, text=col_index)
            else:
                column = Gtk.TreeViewColumn(col["label"], renderer)
                column.set_cell_data_func(renderer, self.__update_cell_active_track)
            #if col.get("cell_type") == CellRendererActiveTrack:
            #    column.set_status(col_index)
            self.append_column(column)

        self.connect("drag_data_get", self.__on_data_get)
        self.connect("drag_data_received", self.__on_data_drop)
        self.connect("button_press_event", self.__on_button_press)

    def __update_cell_active_track(self, _col, cell, model, tree_iter, _data):
        is_active = model.get_value(tree_iter, 1)
        cell.set_active(is_active)

    def __on_row_delete(self, _view):
        model, paths = self.__selection.get_selected_rows()
        with model.handler_block(self.__store_delete_handler_id):
            selected_iters = set()
            for p in paths:
                tree_iter = model.get_iter(p)
                if tree_iter:
                    selected_iters.add(tree_iter)

            if self.__active_iter in selected_iters:
                self.__select_next_iter(exclude=selected_iters)

            for i in selected_iters:
                model.remove(i)
        self.emit("changed")

    def __on_button_press(self, _widget, event):
        if event.type != Gdk.EventType.BUTTON_PRESS:
            return
        if event.get_button().button != 3:
            return
        self.__menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        return True

    def __save_playlist(self, *args):
        self.emit("changed")

    def __on_row_activated(self, _view, path, _column):
        #if event.type != Gdk.EventType.DOUBLE_BUTTON_PRESS:
        #    return
        tree_iter = self.__store.get_iter(path)
        if tree_iter:
            self.__set_active(tree_iter)
            track = self.__store[tree_iter][0]
            self.__active_row_id = self.__store[tree_iter][-1]
            self.__player.stop()
            self.__player.play(track)

    @staticmethod
    def __on_data_get(view, context, selection_data, info, timestamp):
        tree_selection = view.get_selection()
        model, paths = tree_selection.get_selected_rows()
        iters = [model.get_iter(path) for path in paths]
        iter_str = ','.join([model.get_string_from_iter(it) for it in iters])
        selection_data.set(ROW_ATOM, 0, iter_str.encode())

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
            self.emit("changed")

    def __set_active(self, tree_iter):
        if self.__active_iter and self.__store[self.__active_iter]:
            self.__store.set_value(self.__active_iter, 1, False)
        self.__active_iter = tree_iter
        if self.__active_iter and self.__store[self.__active_iter]:
            self.__store.set_value(self.__active_iter, 1, True)

    def __select_next_iter(self, exclude = None):
        if not self.__active_iter:
            return

        next_iter = self.__store.iter_next(self.__active_iter)

        if exclude and self.__active_iter is not None and self.__active_iter in exclude:
            next_iter = self.__select_next_iter(self, exclude=exclude)

        self.__set_active(next_iter)

    def get_selected(self) -> list:
        model, paths = self.__selection.get_selected_rows()
        out = []
        for p in paths:
            tree_iter = self.__store.get_iter(p)
            if tree_iter:
                out.append(self.__store[tree_iter][0])

        return out

    def get_active(self) -> list:
        if self.__active_iter:
            return model[tree_iter][0]

    def get_first_and_activate(self) -> str:
        tree_iter = self.__store.get_iter_first()
        if tree_iter:
            self.__set_active(tree_iter)
            return self.__store[tree_iter][0]

    def get_prev_and_activate(self):
        if self.__active_iter:
            prev_iter = self.__store.iter_previous(self.__active_iter)
            if prev_iter:
                self.__set_active(prev_iter)
                return self.__store[prev_iter][0]

    def get_next_and_activate(self):
        if self.__active_iter:
            next_iter = self.__store.iter_next(self.__active_iter)
            if next_iter:
                self.__set_active(next_iter)
                return self.__store[next_iter][0]

    def add_row(self, row, position_iter=None, insert_after=True):
        #if isinstance(row[1], str):
            # row[1] = row[1] == "True"
        row[1] = False
        if position_iter:
            if insert_after:
                self.__store.insert_after(position_iter, row)
            else:
                self.__store.insert_before(position_iter, row)
        else:
            self.__store.append(row)


    def add_tracks(self, path: str, position_iter=None, insert_after=True) -> bool:
        path = Path(path)
        if not path.exists():
            return False

        if path.is_dir():
            for p in path.iterdir():
                self.add_tracks(str(p), position_iter=None, insert_after=True)
            return True

        info = TrackInfo(path)
        if not info.is_valid():
            return False
        row = [str(path), False,
               info.get_tag("artist"),
               info.get_tag("album"),
               info.get_tag("title"),
               info.get_len_str()]
        self.add_row(row, position_iter, insert_after)


        return True

    def get_cols(self):
        return [k["key"] for k in PLAYLIST_COLS]

    def get_rows(self):
        return [t[:] for t in self.__store]

    @GObject.Property(type=str, default="playlist",
                      flags=GObject.ParamFlags.READABLE)
    def label(self):
        return self.__label

    @GObject.Property(type=int, default=None,
                      flags=GObject.ParamFlags.READABLE)
    def index(self):
        viewport = self.get_parent()
        if not viewport:
            return None
        scrollbox = viewport.get_parent()
        notebook = scrollbox.get_parent()
        if not notebook:
            return None
        return notebook.page_num(scrollbox)

    @property
    def uuid(self):
        return self.__uuid
