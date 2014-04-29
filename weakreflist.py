# Inspired by the `WeakList` module of Gregory Salvan (https://github.com/apieum/weakreflist/).

from weakref import ref

class WeakList(list):

    def _get_value(self, reference):
        try:
            value = reference()
        finally:
            return value

    def _get_ref(self, value):
        try:
            reference = ref(value, self.remove)
        finally:
            return reference

    def __contains__(self, item):
        return list.__contains__(self, self._get_ref(item))

    def __getitem__(self, item):
        return self._get_value(list.__getitem__(self, item))

    def __setitem__(self, i, value):
        return list.__setitem__(self, i, self._get_ref(value))

    def __getslice__(self, i, j):
        _get_value = self._get_value
        return [_get_value(x) for x in list.__getslice__(self, i, j)] #slow?
        
    def __setslice__(self, i, j, values):
        _get_ref = self._get_ref
        return list.__setslice__(self, i, j, (_get_ref(x) for x in values))

    def __iter__(self, *args, **kwargs):
        for x in list.__iter__(self, *args, **kwargs):
            yield self._get_value(x)

    def __repr__(self):
        return "WeakList({!r})".format(list(self))

    def append(self, value):
        list.append(self, self._get_ref(value))
        
    def extend(self, values):
        _get_ref = self._get_ref
        list.extend(self, (_get_ref(x) for x in values))

    def insert(self, i, value):
        list.insert(self, i, self._get_ref(value))
        
    def count(self, value):
        return list.count(self, self._get_ref(value))

    def remove(self, value):
        while list.__contains__(self, value):
            list.remove(self, self._get_ref(value))

    def index(self, value):
        return list.index(self, self._get_ref(value))

    def pop(self, i=-1):
        return list.pop(self, i)
