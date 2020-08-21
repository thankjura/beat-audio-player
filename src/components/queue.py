from gi.repository import GObject

__all__ = ["TracksQueue"]


class TracksQueue(GObject.GObject):
    def __init__(self):
        super().__init__()
        self.__queue = []

    def __index(self, ref):
        for i, r in enumerate(self.__queue):
            if r.get_model() != ref.get_model():
                continue
            if r.get_path() == ref.get_path():
                return i
        return -1

    def __get_positions_for_ref(self, ref):
        out = []
        for i, r in enumerate(self.__queue, 1):
            if r.get_model() != ref.get_model():
                continue
            if r.get_path() == ref.get_path():
                out.append(str(i))

        return ", ".join(out)

    def __update_tracks_positions(self):
        values = {}
        for i, ref in enumerate(self.__queue[:]):
            if not ref or not ref.valid():
                self.__queue.pop(i)
                continue

            model = ref.get_model()
            model.update_position_for_ref(ref, self.__get_positions_for_ref(ref))

    def __remove_track_position(self, ref):
        if ref.valid():
            model = ref.get_model()
            model.update_position_for_ref(ref, None)

    def add(self, track_refs):
        if not track_refs:
            return
        if isinstance(track_refs, (list, set)):
            self.__queue.extend(track_refs)
        else:
            self.__queue.append(track_refs)

        self.__update_tracks_positions()

    def remove(self, track_refs):
        if not track_refs:
            return

        if isinstance(track_refs, (list, set)):
            for ref in track_refs:
                idx = self.__index(ref)
                if idx > -1:
                    self.__queue.pop(idx)
                    self.__remove_track_position(ref)
        else:
            idx = self.__index(track_refs)
            if idx > -1:
                self.__queue.pop(idx)
                self.__remove_track_position(track_refs)

        self.__update_tracks_positions()

    # def add_with_position(self, track_ref, position: int):
    #     if position < 1:
    #         return
    #     placeholder_size = position - len(self.__queue)
    #     if placeholder_size > 0:
    #         self.__queue.extend([None for i in placeholder_size])

    #     self.__queue[position - 1] = track_ref

    @property
    def next(self):
        return self.__queue[0]

    def __bool__(self):
        return len(self.__queue) > 0

