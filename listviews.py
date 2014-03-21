import math
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.widget import Widget
from adapters import ListViewAdapter
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty, DictProperty, ListProperty, AliasProperty, ReferenceListProperty, OptionProperty

class Placeholder(Widget):
    ix = NumericProperty(None)
    text = StringProperty('')
    index = NumericProperty(None)

class DNDListView(FloatLayout, ListViewAdapter):
    container = ObjectProperty(None)
    row_height = NumericProperty(None)
    scrolling = BooleanProperty(False)
    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _wstart = NumericProperty(0)
    _wend = NumericProperty(None, allownone=True)
    _i_offset = NumericProperty(0)
    placeholder = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type("on_scroll_complete")
        self.register_event_type("on_motion_over")
        self.register_event_type("on_motion_out")
        self.register_event_type("on_drag")
        self._trigger_populate = Clock.create_trigger(self._do_layout, -1)
        super(DNDListView, self).__init__(**kwargs)

        self.bind(size=self._trigger_populate, pos=self._trigger_populate)

    def on_data(self, instance, value):
        #print self, '.on_data'
        super(DNDListView, self).on_data(instance, value)
        instance._sizes.clear()
        instance._reset_spopulate()

    def _scroll(self, scroll_y, ceil=math.ceil, floor=math.floor):
        #print self, '._scroll'
        if self.row_height:
            self._scroll_y = scroll_y
            scroll_y = 1 - min(1, max(scroll_y, 0))
            container = self.container
            mstart = (container.height - self.height) * scroll_y
            mend = mstart + self.height

            # convert distance to index
            rh = self.row_height
            istart = int(ceil(mstart / rh))
            iend = int(floor(mend / rh))

            istart = max(0, istart - 1)
            iend = max(0, iend - 1)

            istart -= self._i_offset
            iend += self._i_offset

            if istart < self._wstart:
                rstart = max(0, istart - 10)
                self.populate(rstart, iend)
                self._wstart = rstart
                self._wend = iend
            elif iend > self._wend:
                self.populate(istart, iend + 10)
                self._wstart = istart
                self._wend = iend + 10

    def _do_layout(self, *args):
        self._sizes.clear()
        self.populate()

    def on__sizes(self, instance, value):
        if value:
            container = instance.container
            instance.row_height = rh = next(value.itervalues(), 0) #since they're all the same
            container.height = max((rh*instance.get_count()), container.minimum_height)

    def _reset_spopulate(self, *args):
        #print self, '._reset_spopulate'
        self._wend = None
        self.populate()
        # simulate the scroll again, only if we already scrolled before
        # the position might not be the same, mostly because we don't know the
        # size of the new item.
        if hasattr(self, '_scroll_y'):
            self._scroll(self._scroll_y)

    def populate(self, istart=None, iend=None):
        container = self.container
        sizes = self._sizes
        rh = self.row_height
        get_view = self.get_view
        d = {}

        # ensure we know what we want to show
        if istart is None:
            istart = self._wstart
            iend = self._wend

        # clear the view
        container.clear_widgets()

        # guess only ?
        if iend is not None:

            # fill with a "padding"
            fh = 0
            for x in xrange(istart):
                fh += sizes[x] if x in sizes else rh
            container.add_widget(Widget(size_hint_y=None, height=fh))

            # now fill with real item_view
            index = istart
            while index <= iend:
                item_view = get_view(index)
                index += 1

                if item_view is not None:
                    d[index] = item_view.height
                    container.add_widget(item_view)
        else:
            available_height = self.height
            real_height = 0
            index = self._index
            count = 0

            while available_height > 0:
                item_view = get_view(index)

                if item_view is None:
                    break
                else:
                    d[index] = item_view.height
                    index += 1
                    count += 1
                    container.add_widget(item_view)
                    available_height -= item_view.height
                    real_height += item_view.height

        self._sizes = dict(sizes, **d) 

    def scroll_to(self, index=0):
        #print self, '.scroll_to'
        if not self.scrolling:
            self.scrolling = True
            self._index = index
            self.populate()
            self.dispatch('on_scroll_complete')

    def on_scroll_complete(self, *args):
        self.scrolling = False

    def deparent(self, widget):
        container = self.container
        placeholder = self.placeholder = Placeholder(size=widget.size,
                                                     size_hint_y=None,
                                                     index=widget.index,
                                                     text=widget.text,
                                                     ix=widget.ix,
                                                     opacity=0.0)

        container.add_widget(placeholder, container.children.index(widget))
        container.remove_widget(widget)
        widget.size_hint_x = None
        container.get_root_window().add_widget(widget)
        return

    def reparent(self, instance, widget):
        #Mimic `ListAdapter.create_view`
        data = self.get_data_item(instance.index)
        d = [widget.ix]
        [d.extend([_]) for _ in data[1:]]
        data = tuple(d)
        item_args = self.args_converter(instance.index, data)
        item_args['index'] = widget.index
        new_item = self.list_item(**item_args)

        if self.selection_mode <> 'None':
            new_item.bind(on_release=self.handle_selection)

        container = self.container
        index = container.children.index(widget)
        container.remove_widget(widget)
        container.get_root_window().remove_widget(instance)
        container.add_widget(new_item, index)

    def on_drag(self, widget, d):
        placeholder = self.placeholder

        if not placeholder:
            return self.dispatch('on_motion_over', widget, d)

        children = self.container.children
        p_index = children.index(placeholder)
        _dict = {}

        for child in children:
            if (widget.collide_widget(child) and (child is not placeholder) and (type(child) is not Widget) and not child.disabled):
                c_index = children.index(child)

                if ((widget.center_y <= child.top) and (widget.center_y <= placeholder.y)) or ((widget.center_y >= child.y) and (widget.center_y >= placeholder.top)):
                    children.insert(c_index, children.pop(p_index))
                    #maybe scroll here
                    child_ix = child.ix

                    if d is not None and child.proxy_ref in d:
                        child_ix = d.pop(child.proxy_ref)
                    else:
                        _dict[child.proxy_ref] = placeholder.ix

                    _dict[widget.proxy_ref] = placeholder.ix = child_ix#, child: placeholder.ix}
                    #placeholder.ix, child.ix = child.ix, placeholder.ix
                    placeholder.index = child.index

                return _dict

    def on_motion_over(self, *args):
        return {}

    def on_motion_out(self, widget, _dict):
        if _dict:
            self.parent.dispatch('on_drop', _dict)

class AccordionListView(DNDListView):

    def _lcm(self, a, b):
        a, b = int(a), int(b)
        numerator = a * b

        while b:
            a, b = b, a%b

        if not a:
            return a - 1
        else:
            return numerator/a

    def on__sizes(self, instance, value):
        if value:
            #print self, '.on__sizes'
            #lcm = lambda a, b: ((a * b)/gcd(floor(a),floor(b)))
            sizes = set(value.itervalues()); _min = min(sizes); _max = max(sizes)
            count = instance.get_count() - 1
            instance.container.height = real_height = _max + (_min * count)
            instance.row_height = r_h = real_height / (count + 1)
            numerator = self._lcm(_min, r_h)
            instance._i_offset = int((numerator/_min) - (numerator/r_h)) + 1

    def on_drag(self, instance, d):
        instance = instance.parent
        return super(AccordionListView, self).on_drag(instance, d)
        
    def deparent(self, instance):
        instance = instance.parent
        super(AccordionListView, self).deparent(instance)

class ActionListView(AccordionListView):

    def on_motion_over(self, widget, _d):
        d = {}
        children = self.container.children

        for child in children:
            collision = child.collide_point(*widget.center)

            if collision:
                child.title.state = 'down'
                d = {widget.proxy_ref: child.ix, child.proxy_ref: widget.ix}
            elif child.title.state <> 'normal':
                child.title.state = 'normal'

                if child.proxy_ref in _d:
                    del _d[child.proxy_ref]

        return d

    '''def on_motion_out(self, widget, _dict):
        children = self.container.children

        for child in children:
            if child.title.state == 'down':
                widget.ix = child.ix
                
                if not child.disabled:
                    child.ix = widget.ix
                    d = {widget.text: widget.ix, child.text: child.ix}
                    _dict = dict(_dict, **d)

                self.get_root_window().remove_widget(widget)

        super(ActionListView, self).on_motion_out(widget, _dict)'''

Builder.load_string("""
#:import Scroller scroller.Scroller

<DNDListView>:
    spacing: 1
    container: container_id

    Scroller:
        pos_hint: {'x': 0, 'y': 0}
        scroll_timeout: 0.2
        on_scroll_y: root._scroll(args[1])
        do_scroll_x: False

        GridLayout:
            id: container_id
            cols: 1
            size_hint: 1, None
            spacing: root.spacing
            minimum_height: root.height

<-ActionListView>:
    container: container_id

    GridLayout:
        id: container_id
        cols: 1
        spacing: 0, 1
        size_hint: 1, None
        minimum_height: root.height
        pos_hint: {'x': 0, 'top': 1}

<-QuickListView@DNDListView>:
    container: container
    selection_mode: 'None'

    GridLayout:
        cols: 1
        id: container
        size_hint: 1, 1
""")
