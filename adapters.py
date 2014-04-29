from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty
from weakreflist import WeakList

class ListViewAdapter(object):
    data = ListProperty([])
    cached_views = DictProperty({})
    list_item = ObjectProperty(None)
    selection = ListProperty(WeakList())
    args_converter = ObjectProperty(None)
    selection_mode = OptionProperty('single', options=('None', 'single'))

    def __init__(self, **kwargs):
        self.register_event_type('on_selection_change')
        super(ListViewAdapter, self).__init__(**kwargs)

    def on_data(self, instance, value):
        instance.delete_cache()

        if len(instance.selection) > 0:
            instance.selection[:] = WeakList()

    def on_selection(self, instance, value):
        instance.dispatch('on_selection_change')

    def delete_cache(self, **args):
        self.cached_views.clear()

    def get_count(self):
        return len(self.data)

    def get_data_item(self, index):
        if (0 <= index < self.get_count()):
            return self.data[index]

    def get_view(self, index):
        cached_views = self.cached_views

        if index in cached_views:
            return cached_views[index]
        else:
            item_view = self.create_view(index)

            if item_view:
                cached_views[index] = item_view
                return item_view

    def create_view(self, index):
        item = self.get_data_item(index)

        if item is not None:
            item_args = self.args_converter(index, item)
            item_args['index'] = index
            item_args['listview'] = self.proxy_ref
            view_instance = self.list_item(**item_args)

            if self.selection_mode <> 'None':
                view_instance.bind(on_release=item_args['listview'].handle_selection)

            return view_instance

    def deselect_all(self, *args):
        selection = self.selection

        for each_view in xrange(len(selection)):
            selection.pop().is_selected = False

    def handle_selection(self, view, hold_dispatch=False, *args):
        if view.__self__ in self.selection:
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
        pass
        
