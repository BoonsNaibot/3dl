# Inspired by the `WeakList` module of Gregory Salvan (https://github.com/apieum/weakreflist/).

from weakref import ref

class WeakList(list):

    def _get_object(self, x):
        if isinstance(x, ref):
            x = x()
        return x

    def _get_ref(self, x):
        return ref(x, self.remove)

    def __init__(self, items=[]):
        super(WeakList, self).__init__((self._get_ref(x, self) for x in items))

    def __contains__(self, item):
        return super(WeakList, self).__contains__(self._get_ref(item, self))

    def __getitem__(self, item):
        return self._get_object(super(WeakList, self).__getitem__(item))

    def __getslice__(self, i, j):
        return [self._get_object(x) for x in super(WeakList, self).__getslice__(i, j)] #slow?

    def __iter__(self):
        for x in super(WeakList, self).__iter__():
            yield self._get_object(x)

    def __repr__(self):
        return "WeakList({!r})".format(list(self))

    def __reversed__(self, *args, **kwargs):
        for x in super(WeakList, self).__reversed__(*args, **kwargs):
            yield self._get_object(x)

    def __setitem__(self, i, item):
        super(WeakList, self).__setitem__(i, self._get_ref(item, self))

    def __setslice__(self, i, j, items):
        super(WeakList, self).__setslice__(i, j, (self._get_ref(x, self) for x in items))

    def _remove(self, item):
        while super(WeakList, self).__contains__(item):
            super(WeakList, self).remove(item)

    def append(self, item):
        super(WeakList, self).append(self._get_ref(item, self))

    def count(self, item):
        return super(WeakList, self).count(self._get_ref(item, self))

    def extend(self, items):
        super(WeakList, self).extend((self._get_ref(x, self) for x in items))

    def index(self, item):
        return super(WeakList, self).index(self._get_ref(item, self))

    def insert(self, i, item):
        super(WeakList, self).insert(i, self._get_ref(item, self))

    def remove(self, item):
        self._remove(self._get_ref(item, self))
