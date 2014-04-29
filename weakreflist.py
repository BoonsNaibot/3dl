# Inspired by the `WeakList` module of Gregory Salvan (https://github.com/apieum/weakreflist/).

# -*- coding: utf8 -*-
class WeakList(list):

    def _get_ref(self, value):
        value = self._make_ref(value)
        if list.__contains__(self, value):
            value = list.__getitem__(self, list.index(self, value))
        return value

    def _get_value(self, ref):
        try:
            ref = ref()
        finally:
            return ref

    def _make_ref(self, value):
        try:
            value = weakref.ref(value, self.remove)
        finally:
            return value

    def __contains__(self, item):
        return list.__contains__(self, self._make_ref(item))

    def __getitem__(self, key):
        return self._get_value(list.__getitem__(self, key))

    def __setitem__(self, key, value):
        return list.__setitem__(self, key, self._get_ref(value))

    def __getslice__(self, i, j):
        gV = self._get_value
        return [gV(x) for x in list.__getslice__(self, i, j)] #slow
        
    def __setslice__(self, i, j, y):
        gR = self._get_ref
        return list.__setslice__(self, i, j, (gR(x) for x in y))

    def __iter__(self, *args, **kwargs):
        for x in list.__iter__(self, *args, **kwargs):
            yield self._get_value(x)

    def __repr__(self):
        return "WeakList(%r)" % list(self)

    def append(self, observer):
        list.append(self, self._get_ref(observer))

    def insert(self, i, x):
        list.insert(self, i, self._get_ref(x))

    def remove(self, value):
        value = self._make_ref(value)
        while list.__contains__(self, value):
            list.remove(self, value)

    def index(self, *args, **kwargs):
        return list.index(self, *map(self._make_ref, args), **kwargs)

    def pop(self, value):
        return list.pop(self, value)
