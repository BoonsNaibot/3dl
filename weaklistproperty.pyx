class ObservableWeakList(WeakList):
    # Internal class to observe changes inside a WeakList.
    def __init__(self, *largs):
        self.prop = largs[0]
        self.obj = ref(largs[1])
        super(ObservableWeakList, self).__init__(*largs[2:])

    def __setitem__(self, key, value):
        super(ObservableWeakList, self).__setitem__(key, value)
        observable_list_dispatch(self)

    def __delitem__(self, key):
        super(ObservableWeakList, self).__delitem__(key)
        observable_list_dispatch(self)

    def __setslice__(self, *largs):
        super(ObservableWeakList, self).__setslice__(*largs)
        observable_list_dispatch(self)

    def __delslice__(self, *largs):
        super(ObservableWeakList, self).__delslice__(*largs)
        observable_list_dispatch(self)

    def __iadd__(self, *largs):
        super(ObservableWeakList, self).__iadd__(*largs)
        observable_list_dispatch(self)

    def __imul__(self, *largs):
        super(ObservableWeakList, self).__imul__(*largs)
        observable_list_dispatch(self)

    def append(self, *largs):
        super(ObservableWeakList, self).append(*largs)
        observable_list_dispatch(self)

    def remove(self, *largs):
        super(ObservableWeakList, self).remove(*largs)
        observable_list_dispatch(self)

    def insert(self, *largs):
        super(ObservableWeakList, self).insert(*largs)
        observable_list_dispatch(self)

    def pop(self, *largs):
        cdef object result = super(ObservableWeakList, self).pop(*largs)
        observable_list_dispatch(self)
        return result

    def extend(self, *largs):
        super(ObservableWeakList, self).extend(*largs)
        observable_list_dispatch(self)

    def sort(self, *largs):
        super(ObservableWeakList, self).sort(*largs)
        observable_list_dispatch(self)

    def reverse(self, *largs):
        super(ObservableWeakList, self).reverse(*largs)
        observable_list_dispatch(self)


cdef class WeakListProperty(Property):
    '''Property that represents a list.

    :Parameters:
        `default`: list, defaults to WeakList([])?
            Specifies the default value of the property.
    '''

    def __init__(self, defaultvalue=None, **kw):
        defaultvalue = defaultvalue or WeakList([])
        super(WeakListProperty, self).__init__(defaultvalue, **kw)

    cpdef link(self, EventDispatcher obj, str name):
        Property.link(self, obj, name)
        cdef PropertyStorage ps = obj.__storage[self._name]
        ps.value = ObservableWeakList(self, obj, ps.value)

    cdef check(self, EventDispatcher obj, value):
        if Property.check(self, obj, value):
            return True
        if type(value) is not ObservableWeakList:
            raise ValueError('%s.%s accept only ObservableWeakList' % (
                obj.__class__.__name__,
                self.name))

    cpdef set(self, EventDispatcher obj, value):
        value = ObservableWeakList(self, obj, value)
        Property.set(self, obj, value)
