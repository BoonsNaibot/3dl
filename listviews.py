from math import ceil, floor
from kivy.clock import Clock
from kivy.lang import Builder
from datetimewidgets import Day
from weakreflist import WeakList
from kivy.uix.widget import Widget
from kivy.uix.layout import Layout
from adapters import ListViewAdapter
from datetime import date, timedelta
from weakref import WeakKeyDictionary
from itertools import repeat, izip, chain
from kivy.properties import AliasProperty, BooleanProperty, DictProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty, VariableListProperty

class Placeholder(Widget):
    ix = NumericProperty(None)
    text = StringProperty('')
    index = NumericProperty(None)

    def on_touch_move(self, touch):
        return True

class ListContainerLayout(Layout):
    spacing = NumericProperty(0)
    padding = NumericProperty(0)
    _children = ListProperty(WeakList())
    
    def _get_children(self):
        return self._children
        
    def _set_children(self, children):
        if type(children) is list:
            children = WeakList(children)
        if self._children <> children:
            self._children = children
        else:
            return False
        
    children = AliasProperty(_get_children, _set_children)

    def __init__(self, **kwargs):
        super(ListContainerLayout, self).__init__(**kwargs)
        self.bind(children=self._trigger_layout,
                  pos=self._trigger_layout,
                  pos_hint=self._trigger_layout,
                  size_hint=self._trigger_layout,
                  size=self._trigger_layout)

    def do_layout(self, *args, **kwargs):
        if 1 not in self.size:
            # Just like `FloatLayout`
            w, h = kwargs.get('size', self.size)
            x, y = kwargs.get('pos', self.pos)
            spacing = self.spacing
            place = (y + h) - self.padding

            for c in reversed(self.children):
                c.width = w
                c.x = x
                c.top = place
                #y += c.height + spacing
                place -= (c.height + spacing)

    def clear_widgets(self, *args):
        for _ in xrange(len(self.children)):
            child = self.children.pop(-1)
            self.canvas.remove(child.canvas)
            child.parent = None

class DNDListView(Widget, ListViewAdapter):
    container = ObjectProperty(None)
    row_height = NumericProperty(None)
    scrolling = BooleanProperty(False)
    _index = NumericProperty(0)
    _sizes = DictProperty({})
    _wstart = NumericProperty(0)
    _wend = NumericProperty(None, allownone=True)
    _i_offset = NumericProperty(0)
    spacing = NumericProperty(1)
    placeholder = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type("on_motion_over")
        self.register_event_type("on_motion_out")
        self.register_event_type("on_drag")
        self._trigger_populate = Clock.create_trigger(self._do_layout, -1)
        super(DNDListView, self).__init__(**kwargs)
        self.bind(pos=self._trigger_populate)

    def on_data(self, instance, value):
        super(DNDListView, self).on_data(instance, value)
        instance._sizes.clear()
        instance._reset_spopulate()

    def _scroll(self, scroll_y):
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
            container.height = (rh + instance.spacing) * instance.get_count()

    def _reset_spopulate(self, *args):
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
        container.padding = 0

        # guess only ?
        if iend is not None:
            spacing = self.spacing
            fh = 0

            # fill with a "padding"
            for x in xrange(istart):
                fh += sizes[x]+spacing if x in sizes else rh+spacing
            #container.add_widget(Widget(size_hint_y=None, height=fh))
            container.padding = fh

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
            real_height = count = 0
            index = self._index

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

        new_sizes = dict(sizes, **d)

        if new_sizes <> sizes:
            self._sizes = new_sizes

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

    def reparent(self, instance, widget, indices):
        placeholder = instance.listview.placeholder
        #Mimic `ListAdapter.create_view`
        data = ((widget.ix,) + instance.listview.get_data_item(instance.index)[1:])
        item_args = self.args_converter(widget.index, data)
        item_args['index'] = widget.index
        new_item = self.list_item(**item_args)

        if self.selection_mode <> 'None':
            new_item.bind(on_release=self.handle_selection)

        container = self.container
        index = container.children.index(widget)
        container.remove_widget(widget)
        container.get_root_window().remove_widget(instance)
        container.add_widget(new_item, index)
        _l = lambda *_: self.parent.dispatch('on_drop', indices)
        Clock.schedule_once(_l, 0.055)

        if placeholder.parent:
            placeholder.parent.remove_widget(placeholder)
        instance.state = 'normal'

    def on_drag(self, widget, indices):
        placeholder = self.placeholder

        if not placeholder:
            return self.dispatch('on_motion_over', widget, indices)

        children = self.container.children
        p_index = children.index(placeholder)
        d = WeakKeyDictionary({widget: placeholder.ix})

        for child in children:
            if (widget.collide_widget(child) and (child is not placeholder) and (type(child) is not Widget)):
                c_index = children.index(child)

                if ((widget.center_y <= child.top) and (widget.center_y <= placeholder.y)) or ((widget.center_y >= child.y) and (widget.center_y >= placeholder.top)):
                    children.insert(c_index, children.pop(p_index))
                    placeholder.index, child.index = c_index, p_index
                    #maybe scroll here
                    child_ix = child.ix

                    if child in indices:
                        child_ix = indices.pop(child)
                    else:
                        d[child] = placeholder.ix

                    d[widget] = placeholder.ix = child_ix
                    break

        _dict = WeakKeyDictionary(dict(indices, **d))
        return _dict

    def on_motion_over(self, *args):
        return WeakKeyDictionary()

    def on_motion_out(self, widget, l):
        if l:
            self.parent.dispatch('on_drop', l)

class AccordionListView(DNDListView):
    
    def _get_selection(self):
        return self.parent.selection
        
    selection = AliasProperty(_get_selection, None)

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
            spacing = instance.spacing
            sizes = frozenset(value.itervalues()); _min = min(sizes) + spacing; _max = max(sizes) + spacing
            count = instance.get_count() - 1
            real_height = _max + (_min * count)

            if real_height <> instance.container.height:
                instance.container.height = real_height
                instance.row_height = r_h = real_height / (count + 1)
                numerator = instance._lcm(_min, r_h)
                instance._i_offset = int((numerator/_min) - (numerator/r_h)) + 1

    def on_drag(self, instance, *args):
        instance = instance.parent
        return super(AccordionListView, self).on_drag(instance, *args)
        
    def deparent(self, instance):
        instance = instance.parent
        super(AccordionListView, self).deparent(instance)

    def on_motion_out(self, widget, indices):
        args = []

        if indices:
            point = widget.center
            page = widget.screen.page
            deleting = self.placeholder is None
            #deleting = widget.listview.__self__ is not self

            for k, v in indices.iteritems():

                if (deleting and (not k.collide_point(*point))):
                    k.index -= 1
                elif k.disabled:
                    args.append((u"", u"", 0, u"", v, page))
                else:
                    args.append((k.text, k.when, int(k.why), k.how, v, page))

        return tuple(args)

class ActionListView(AccordionListView):

    def on_motion_over(self, instance, indices):
        d = WeakKeyDictionary({instance: instance.listview.placeholder.ix})

        for child in self.container.children:
            collision = child.collide_point(*instance.center)

            if collision:
                child.state = 'down'
                d.update({instance: child.ix, child: instance.ix})
            elif child.state <> 'normal':
                child.state = 'normal'

                if child in indices:
                    del indices[child]

        _dict = WeakKeyDictionary(dict(indices, **d))
        return _dict

class DatePickerListView(AccordionListView):
    spacing = NumericProperty(0)
    
    def __init__(self, **kwargs):
        self.register_event_type('on_populated')
        super(DatePickerListView, self).__init__(**kwargs)
    
    def on_populated(self, root):
        cached_views = self.cached_views
            
        if len(cached_views) == 6:
            year, month = root.date.year, root.date.month
            
            if (year, month) <> (root.year, root.month):
                root.year, root.month = year, month
                _timedelta = timedelta
                today = date.today()
                _repeat = repeat
                ravel = chain.from_iterable
        
                def _args_converter(date_cursor, delta):
                    date_label = Day(text=str(date_cursor.day))
        
                    if date_cursor < today:
                        date_label.disabled = True
                    elif ((delta < 0) or (month <> date_cursor.month)):
                        date_label.in_month = False
                    return date_label
    
                _date = date(year, month, 1)
                dt = _date.isoweekday()# - instance.type_of_calendar
        
                for child in cached_views.itervalues():
                    child.title.clear_widgets()
        
                these = ravel(_repeat(i, 7) for i in sorted(cached_views.itervalues(), key=cached_views.get))
                those = (_args_converter((_date+timedelta(days=delta)), delta) for delta in xrange(-dt, ((7*6)-dt)))
                _on_release = self.handle_selection
        
                for this, that in izip(these, those):
                    that.bind(on_release=_on_release)
                    that.week = this
                    this.title.add_widget(that)
    
    def _do_layout(self, *args):
        super(DatePickerListView, self)._do_layout(*args)
        self.dispatch('on_populated', self.parent)

Builder.load_string("""
#:import Scroller scroller.Scroller

<DNDListView>:
    container: container_id

    Scroller:
        pos: root.pos
        size: root.size
        on_scroll_y: root._scroll(args[1])

        ListContainerLayout:
            id: container_id
            #pos_hint: {'x': 0}
            #size_hint: 1, None
            x: root.x
            width: root.width
            spacing: root.spacing

<-ActionListView>:
    container: container_id
    size_hint: 1, None
    height: container_id.height

    ListContainerLayout:
        id: container_id
        x: root.x
        top: root.top
        size: root.size
        spacing: root.spacing

<-QuickListView@DNDListView>:
    container: container_id
    size: container_id.size
    selection_mode: 'None'

    GridLayout:
        cols: 1
        id: container_id
        pos: root.pos
        size: root.size
""")
