cdef extern from "Python.h":
    object PyWeakref_NewRef(object ob, object callback)
    object PyWeakref_GetObject(object ref)
    void Py_XINCREF(object o)


cdef class WeakList(list):
    cpdef _remove(object self, object item)
