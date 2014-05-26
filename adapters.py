from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty, WeakListProperty
from kivy.weakreflist import WeakList
import objgraph, random

class ListViewAdapter(object):
    data = ListProperty([])
    cached_views = DictProperty({})
    list_item = ObjectProperty(None)
    selection = WeakListProperty(WeakList())
    args_converter = ObjectProperty(None)
    selection_mode = OptionProperty('single', options=('None', 'single'))

    def __init__(self, **kwargs):
        self.register_event_type('on_selection_change')
        super(ListViewAdapter, self).__init__(**kwargs)

    def on_data(self, instance, value):
        instance.delete_cache()

        if len(instance.selection) > 0:
            instance.selection[:] = []

    def on_selection(self, instance, value):
        instance.dispatch('on_selection_change')

    def delete_cache(self, *args):
        self.cached_views.clear()
        self.container.canvas.clear()

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if (0 <= index < self.get_count()):
            return self.data[index]

    def get_view(self, index):
        if index in self.cached_views:
            return self.cached_views[index]
        else:
            item_view = self.create_view(index)

            if item_view:
                self.cached_views[index] = item_view
                return item_view

    def create_view(self, index):
        item = self.get_data_item(index)

        if item is not None:
            item_args = self.args_converter(index, item)
            item_args['index'] = index
            return self.list_item(**item_args)

    def deselect_all(self, *args):
        selection = self.selection

        for each_view in xrange(len(selection)):
            selection.pop().is_selected = False

    def handle_selection(self, view, hold_dispatch=False, *args):
        if view in self.selection:
            self.deselect_item_view(view)            
        elif self.selection_mode == 'single':
            self.deselect_all()
            self.select_item_view(view)
        if not hold_dispatch:
            self.dispatch('on_selection_change')

    def select_item_view(self, view):
        view.is_selected = True
        self.selection.append(view)

    def deselect_item_view(self, view):
        view.is_selected = False
        self.selection.remove(view)

    def on_selection_change(self, *args):
        #pass
        if self.selection:
            from listscreen import ListScreenItem
            objgraph.show_growth()
            print '...'
            roots = objgraph.get_leaking_objects()
            objgraph.show_most_common_types(objects=roots)
            print '...'
            #objgraph.show_refs(roots[:3], refcounts=True, filename='sad.png')
            #objgraph.show_chain(objgraph.find_backref_chain(self.selection[0].__self__, objgraph.is_proper_module),filename='chain.png')
            objgraph.show_backrefs(self.selection[0].__self__, filename='sample-backref-graph.png')
            print '...'
            
