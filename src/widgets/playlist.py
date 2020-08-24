from pathlib import Path
from urllib.parse import unquote
from itertools import compress

from gettext import gettext as _
from gi.repository import Gtk, Gdk, GObject
from uuid import uuid4

from beat.widgets.cell_renderers import *
from beat.components.store import PlayListStore, PLAYLIST_COLS
from beat.utils.track_info import TrackInfo
from beat.components.queue_manager import QueueState

__all__ = ["PlayList"]

TARGETS = [
        ('GTK_LIST_BOX_ROW',    Gtk.TargetFlags.SAME_WIDGET, 0)
]

ROW_ATOM = Gdk.Atom.intern_static_string("GTK_LIST_BOX_ROW")


class PlayList(Gtk.TreeView):
    __gtype_name__ = "PlayList"


    __gsignals__ = {
        "changed": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    def __init__(self, app, label, uuid=None, saved=False):
        super().__init__()
        self.__app = app
        self.__label = label
        self.__uuid = uuid if uuid else str(uuid4())
        self.__selection = self.get_selection()
        self.__saved = saved

        # property
        # self.props.enable_search = True
        self.__selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        # store
        self.__store = PlayListStore()
        self.__store.connect("rows-reordered", self.__save_playlist)

        # queue
        self.__queue = self.__app.props.queue
        self.__queue.connect("notify::state", self.__on_queue_state)

        self.props.activate_on_single_click = False
        self.set_model(self.__store)

        # right click menu
        self.__menu = Gtk.Menu()
        menu_add_to_queue_item = Gtk.MenuItem(_("Add to queue"))
        menu_add_to_queue_item.connect("activate", self.__on_add_to_queue)
        self.__menu_remove_from_queue_item = Gtk.MenuItem(_("Remove from queue"))
        self.__menu_remove_from_queue_item.connect("activate", self.__on_remove_from_queue)
        menu_delete_item = Gtk.MenuItem(_("Delete"))
        menu_delete_item.connect("activate", self.__on_row_delete)
        self.__menu.add(menu_add_to_queue_item)
        self.__menu.add(self.__menu_remove_from_queue_item)
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
            if issubclass(col.get("cell_type"), Gtk.CellRendererText):
                column = Gtk.TreeViewColumn(col["label"], renderer, text=col_index)
            elif col.get("cell_type") == CellRendererActiveTrack:
                column = Gtk.TreeViewColumn(col["label"], renderer)
                column.set_min_width(24)
                column.set_cell_data_func(renderer, self.__update_cell_active_track)
            else:
                column = Gtk.TreeViewColumn(col["label"], renderer)

            self.append_column(column)

        self.connect("drag_data_get", self.__on_data_get)
        self.connect("drag_data_received", self.__on_data_drop)
        self.connect("button_press_event", self.__on_button_press)

    def __on_queue_state(self, queue, _state):
        active_ref = queue.active_ref
        if not active_ref:
            self.__store.set_active_ref(None)
            return

        if self.__store.active_ref != active_ref:
            self.__store.set_active_ref(None)

        model = active_ref.get_model()
        state = queue.state
        if self.__store == model:
            self.__store.set_active_ref(active_ref)
            if state == QueueState.PLAYING:
                self.__store.set_state_for_active_ref("play")
            elif state == QueueState.PAUSED:
                self.__store.set_state_for_active_ref("pause")
            else:
                self.__store.set_state_for_active_ref("stop")

    def __update_cell_active_track(self, _col, cell, model, tree_iter, _data):
        ref = Gtk.TreeRowReference.new(self.__store, self.__store.get_path(tree_iter))
        cell.set_state(self.__store.get_state_for_iter(tree_iter))

    def __get_selected_refs(self):
        model, paths = self.__selection.get_selected_rows()
        selected_refs = set()
        for p in paths:
            ref = Gtk.TreeRowReference.new(model, p)
            selected_refs.add(ref)

        return selected_refs

    def __on_row_delete(self, _view):
        selected_refs = self.__get_selected_refs()
        self.__store.remove_refs(selected_refs)
        self.__queue.remove(selected_refs)
        self.emit("changed")

    def __on_add_to_queue(self, _view):
        selected_refs = self.__get_selected_refs()
        self.__queue.add(selected_refs)

    def __on_remove_from_queue(self, _view):
        selected_refs = self.__get_selected_refs()
        self.__queue.remove(selected_refs)

    def __on_button_press(self, _widget, event):
        if event.type != Gdk.EventType.BUTTON_PRESS:
            return
        if event.get_button().button != 3:
            return
        data = self.get_path_at_pos(event.x, event.y)
        if data:
            path = data[0]
            if not self.__selection.path_is_selected(path):
                self.__selection.unselect_all()
                self.__selection.select_path(path)

        selected_refs = self.__get_selected_refs()
        has_position_ref = False
        for ref in selected_refs:
            if self.__store.get_position_for_ref(ref):
                has_position_ref = True
                break
        if has_position_ref:
            self.__menu_remove_from_queue_item.show()
        else:
            self.__menu_remove_from_queue_item.hide()

        self.__menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
        return True

    def __save_playlist(self, *args):
        self.emit("changed")

    def __on_row_activated(self, _view, path, _column):
        ref = Gtk.TreeRowReference(self.__store, path)
        self.__store.set_active_ref(ref)
        self.__queue.play_ref(ref)

    def play(self, ref):
        self.__store.set_active_ref(ref)
        if ref:
            self.__queue.play_ref(ref)

    def __on_data_get(self, view, context, selection_data, info, timestamp):
        model, paths = self.__selection().get_selected_rows()
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
                if not p:
                    continue
                filepath = unquote(p.strip().replace("file://", "", 1))
                self.add_tracks(filepath, position_iter, insert_after)
            self.emit("changed")

    def add_row(self, row, position_iter=None, insert_after=True):
        ref = self.__store.add_row(row, position_iter=position_iter, insert_after=insert_after)
        return ref

    def add_tracks(self, path: str, position_iter=None, insert_after=True) -> list:
        path = Path(path)
        out = []
        if not path.exists():
            return out

        if path.is_dir():
            for p in path.iterdir():
                out.extend(self.add_tracks(str(p), position_iter=position_iter, insert_after=insert_after))
            return out

        try:
            info = TrackInfo(path)
        except:
            return out

        row = {"src":   str(path),
               "artist": info.artist,
               "album":  info.album,
               "title":  info.title,
               "length": info.duration_str}

        ref = self.add_row(row, position_iter, insert_after)
        out.append(ref)

        return out

    def get_cols(self):
        return [k["key"] for k in PLAYLIST_COLS if not k["key"].startswith("_")]

    def get_rows(self):
        mask = [not k["key"].startswith("_") for k in PLAYLIST_COLS]
        return [compress(t, mask) for t in self.__store]

    @property
    def label(self):
        return self.__label

    @property
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

    @property
    def active_ref(self):
        return self.__store.active_ref

    def is_saved(self):
        return self.__saved

    def set_saved(self, saved):
        self.__saved = saved

    def get_first_and_select(self):
        return self.__store.get_first_and_select()
