from kivy.properties import ObjectProperty, NumericProperty, ListProperty, OptionProperty, StringProperty, BooleanProperty, DictProperty, AliasProperty
from kivy.uix.screenmanager import SlideTransition, Screen
from kivy.graphics.transformation import Matrix
from weakref import ref, WeakKeyDictionary
from kivy.uix.textinput import TextInput
from parents import Widget, FloatLayout
from kivy.animation import Animation
from weakreflist import WeakList
from kivy.vector import Vector
from math import radians, ceil
from kivy.lang import Builder
from kivy.clock import Clock

class NavBar(FloatLayout):
    text = StringProperty('')
    shorten = BooleanProperty(False)
    font_size = NumericProperty(0)
    font_name = StringProperty('Walkway Bold.ttf')

class StatusBar(Widget):

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.parent.dispatch('on_status_bar')
            return True

class BoundedTextInput(TextInput):
    max_chars = NumericProperty(31)
    active_color = ListProperty([])
    inactive_color = ListProperty([])

    def insert_text(self, substring, from_undo=False):
        #substring = unicode(substring, encoding=chardetect(substring)["encoding"])

        if not from_undo and (len(self.text) + len(substring) > self.max_chars):
            return
        super(BoundedTextInput, self).insert_text(substring, from_undo)

    def on_touch_down(self, touch):
        super(BoundedTextInput, self).on_touch_down(touch)
        return self.collide_point(*touch.pos)

class NewItemWidget(FloatLayout):
    state = OptionProperty('normal', options=('edit', 'normal'))
    hint_text = StringProperty('')

    def __init__(self, **kwargs):
        self.register_event_type('on_text_validate')
        super(NewItemWidget, self).__init__(**kwargs)

    def on_state(self, instance, value):
        screen = instance.parent

        if value == 'edit':
            screen.polestar = ref(instance)
        elif screen.polestar():
            screen.polestar = lambda : None

    def on_text_validate(self, *args):
        pass

class StencilLayout(FloatLayout):
    pass

class Screen_(Screen):
    root_directory = ObjectProperty(None)
    keyboard_height = NumericProperty(None)
    polestar = ObjectProperty(lambda : None)

    def __init__(self, **kwargs):
        self._anim = lambda : None
        self.register_event_type('on_delete')
        self.register_event_type('on_complete')
        self.register_event_type('on_status_bar')
        self.register_event_type('on_screen_change')
        super(Screen_, self).__init__(**kwargs)

    def on_polestar(self, instance, value):
        value = value()

        if (value and (value.state == 'edit')):
            y = instance.to_window(*value.pos)[1]
            kh = instance.keyboard_height
            #center_y = 0.38*instance.get_root_window().height

            if y < kh:
                _anim = Animation(y=(kh-y), t='out_expo', d=0.3)
                instance._anim = ref(_anim)
                _anim.start(instance)

        elif instance.y <> 0:
            _anim = Animation(y=0, t='out_expo', d=0.3)
            instance._anim = ref(_anim)
            _anim.start(instance)

    def on_touch_down(self, touch):
        if self._anim() is None:
            polestar = self.polestar()

            if polestar:
                touch.push()
                touch.apply_transform_2d(self.to_local)
                ret = polestar.dispatch('on_touch_down', touch)
                touch.pop()

                if not ret:
                    self.polestar = lambda : None
                return ret

            else:
                return super(Screen_, self).on_touch_down(touch)

    def on_screen_change(self, destination, kwargs, transition=SlideTransition):
        manager =  self.manager
        transition = transition(**kwargs)
        manager.transition = transition
        manager.current = destination

    def add_widget(self, *args):
        super(Screen_, self).add_widget(*args)
        args[0].parent = self.proxy_ref

    def on_delete(self, *args):
        pass

    def on_complete(self, *args):
        pass

    def on_status_bar(self, *args):
        pass

class Selectable(object):
    index = NumericProperty(None)
    is_selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Selectable, self).__init__(**kwargs)

    def on_is_selected(self, instance, value):
        if value:
            instance.select()
        else:
            instance.deselect()

    def select(self, *args):
        pass

    def deselect(self, *args):
        pass

    def on_release(self):
        pass

class ButtonRoot(Widget):
    text = StringProperty('')
    index = NumericProperty(None)
    aleft = BooleanProperty(False)
    font_size = NumericProperty(0)
    markup = BooleanProperty(False)
    shorten = BooleanProperty(False)
    font_name = StringProperty('Walkway Bold.ttf')
    state_color = ListProperty([1.0, 1.0, 1.0, 0.0])
    text_color = ListProperty([0.0, 0.824, 1.0, 1.0])

    def on_state(self, *args):
        pass

    def on_touch_down(self, touch):
        if not self.disabled:
            touch.grab(self)
            touch.ud[self] = True
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
            
    def cancel(self):
        self.state = 'normal'

class Clickable(ButtonRoot):
    state = OptionProperty('normal', options=('normal', 'down'))

    def __init__(self, **kwargs):
        self.register_event_type('on_press')
        self.register_event_type('on_release')
        self._press_ = Clock.create_trigger(self._trigger_press, 0.0625)
        self._release_ = Clock.create_trigger(self._trigger_release, .15)        
        super(Clickable, self).__init__(**kwargs)

    def _trigger_press(self, dt):
        if ((self.state == 'normal') and not self.disabled):
            self.state = 'down'
            self.dispatch('on_press')
        else:
            return False

    def _trigger_release(self, dt):
        if self.state == 'normal':
            self.dispatch('on_release')
        else:
            return False

    def on_touch_down(self, touch):
        if self.state == 'normal':
            sup = super(ButtonRoot, self).on_touch_down(touch)

            if sup:
                return sup
            else:
                self._press_()

        return super(Clickable, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':
                sup = super(ButtonRoot, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    self.state = 'normal'
                    self._release_()

        return super(Clickable, self).on_touch_up(touch)

    def on_press(self):
        pass

    def on_release(self):
        pass
    
    def cancel(self):
        Clock.unschedule(self._trigger_press)
        self._press_ = Clock.create_trigger(self._trigger_press, 0.0625)
        super(Clickable, self).cancel()

class DelayedClickable(Clickable):

    def _trigger_release(self, dt):
        if self.state == 'down':
            self.dispatch('on_release')
            self._do_release()
        else:
            return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'down':
                sup = super(ButtonRoot, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    self._release_()
            return super(Clickable, self).on_touch_up(touch)

class Deletable(ButtonRoot):
    state = OptionProperty('normal', options=('normal', 'delete'))
    delete_button = ObjectProperty(lambda : None)
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        self._anim = lambda : None
        self.register_event_type('on_delete_out')
        super(Deletable, self).__init__(**kwargs)

    def on_state(self, instance, value):
        if ((value <> 'delete') and instance.delete_button()):
            #instance.unbind(right=instance.delete_button.right, y=instance.delete_button.y)
            instance.dispatch('on_delete_out', instance.layout)
            instance.screen.polestar = lambda : None
        elif value == 'delete':
            deletebutton = DeleteButton(size=(instance.size[1], instance.size[1]),
                                        pos=((instance.right-instance.size[1]), instance.pos[1]),
                                        button=instance.proxy_ref)
            instance.add_widget(deletebutton, 1)
            instance.delete_button = ref(deletebutton)
            #instance.bind(right=deletebutton.right, y=deletebutton.y)
            instance.screen.polestar = ref(instance)
        super(Deletable, self).on_state(instance, value)

    def on_touch_down(self, touch):
        if self._anim() is not None:
            return True
        elif self.state == 'delete':
            sup = super(ButtonRoot, self).on_touch_down(touch)

            if not sup:
                self.state = 'normal'
            return True

        else:
            return super(Deletable, self).on_touch_down(touch)

    def on_touch_move(self, touch):

        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state in ('down', 'normal'):
                sup = super(ButtonRoot, self).on_touch_move(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                elif ((touch.dx < -20) and not self.delete_button()):
                    self.state = 'delete'

            if self.state == 'delete':
                new_pos = max(self.delete_button().x, min((self.layout.right+touch.dx), self.right))
                self.layout.right = new_pos
                return True
        
        elif ((self.state == 'delete') or (self.state in ('down', 'normal') and self.collide_point(*touch.pos) and ((touch.dx < -20) and not self.delete_button()))):
            return True
        return super(Deletable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'delete':
                sup = super(ButtonRoot, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    touch.ungrab(self)
                    layout = self.layout
                    db = self.delete_button()

                    if (layout.right < db.center_x):
                        _anim = Animation(right=db.x, t='out_quad', d=0.2)
                        self._anim = ref(_anim)
                        _anim.start(layout)
                    else:
                        self.state = 'normal'
                    return True

        return super(Deletable, self).on_touch_up(touch)

    def on_delete_out(self, layout, *args):

        def _do_release(a, widget):
            parent = widget.parent
            parent.remove_widget(parent.delete_button())
            parent.delete_button = lambda : None
        
        _anim = Animation(right=self.right, t='out_quad', d=0.2)
        _anim.bind(on_complete=_do_release)
        self._anim = ref(_anim)
        _anim.start(layout)

class Completable(ButtonRoot):
    screen = ObjectProperty(None)
    complete_button = ObjectProperty(lambda : None)
    state = OptionProperty('normal', options=('normal', 'complete'))

    def __init__(self, **kwargs):
        self._anim = lambda : None
        self.register_event_type('on_complete_out')
        super(Completable, self).__init__(**kwargs)

    def on_state(self, instance, value):
        if ((value <> 'complete') and instance.complete_button()):
            #instance.unbind(pos=instance.complete_button.pos)
            instance.dispatch('on_complete_out', instance.layout)
            instance.screen.polestar = lambda : None
        elif value == 'complete':
            completebutton = CompleteButton(size=(instance.size[1], instance.size[1]), pos=instance.pos, button=instance.proxy_ref)
            instance.add_widget(completebutton, 1)
            instance.complete_button = ref(completebutton)
            #instance.bind(pos=completebutton.pos)
            instance.screen.polestar = ref(instance)
        super(Completable, self).on_state(instance, value)

    def on_touch_down(self, touch):
        if self._anim() is not None:
            return True
        elif self.state == 'complete':
            sup = super(ButtonRoot, self).on_touch_down(touch)

            if not sup:
                self.state = 'normal'
            return True

        else:
            return super(Completable, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state in ('down', 'normal'):
                sup = super(ButtonRoot, self).on_touch_move(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                elif ((touch.dx > 20) and not self.complete_button()):
                    self.state = 'complete'

            if self.state == 'complete':
                new_pos = max(self.x, min((self.layout.x+touch.dx), self.complete_button().right))
                self.layout.x = new_pos
                return True

        elif ((self.state == 'complete') or (self.state in ('down', 'normal') and self.collide_point(*touch.pos) and ((touch.dx > 20) and not self.complete_button()))):
            return True
        return super(Completable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'complete':
                sup = super(ButtonRoot, self).on_touch_up(touch)

                if sup:
                    touch.ungrab(self)
                    return sup
                else:
                    touch.ungrab(self)
                    layout = self.layout
                    cb = self.complete_button()

                    if (layout.x > cb.center_x):
                        _anim = Animation(x=cb.right, t='out_quad', d=0.2)
                        self._anim = ref(_anim)
                        _anim.start(layout)
                    else:
                        self.state = 'normal'
                    return True

        return super(Completable, self).on_touch_up(touch)

    def on_complete_out(self, layout, *args):

        def _do_release(a, widget):
            parent = widget.parent
            parent.remove_widget(parent.complete_button())
            parent.complete_button = lambda : None
        
        _anim = Animation(x=self.x, t='out_quad', d=0.2)
        _anim.bind(on_complete=_do_release)
        self._anim = ref(_anim)
        _anim.start(layout)

class Editable(ButtonRoot):
    state = OptionProperty('normal', options=('normal', 'edit'))
    textinput = ObjectProperty(lambda : None)
    _double_tap_time = NumericProperty(0.0)
    _switch = BooleanProperty(False)
    max_chars = NumericProperty(31)
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_text_validate')
        super(Editable, self).__init__(**kwargs)
            
    def on__switch(self, instance, value):
        if value:
            Clock.schedule_interval(instance._double_tap_interval, 0.1)

    def _double_tap_interval(self, dt):
        if (self._switch and not self.disabled):
            self._double_tap_time += dt

            if self._double_tap_time >= 0.250:
                self._switch = False

        else:
            self._double_tap_time = 0.0
            return False

    def on_touch_down(self, touch):
        if self.state == 'edit':
            sup = super(ButtonRoot, self).on_touch_down(touch)

            if not sup:
                self.state = 'normal'
            return True

        elif self.state in ('down', 'normal'):
            if not self._switch:
                self._switch = True
            else:
                self.state = 'edit'
                return True

        return super(Editable, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if (self.state == 'edit'):
            return True
        return super(Editable, self).on_touch_move(touch)

    def on_state(self, instance, value):
        if value not in ('normal', 'down'):
            instance._switch = False
        if ((value <> 'edit') and instance.textinput()):
            #instance.unbind(pos=instance.textinput.pos, size=instance.textinput.size)
            instance.remove_widget(instance.textinput())
            instance.textinput = lambda : None
            instance.screen.polestar = lambda : None
        elif value == 'edit':
            t = BoundedTextInput(text=instance.text,
                                 size_hint=(None, None),
                                 max_chars=instance.max_chars,
                                 font_size=instance.label.font_size,
                                 font_name=instance.label.font_name,
                                 pos=instance.pos,
                                 size=instance.size,
                                 multiline=False)
            instance.add_widget(t)
            instance.textinput = ref(t)
            #instance.bind(pos=t.pos, size=t.size)
            t.bind(on_text_validate=instance.on_text_validate, focus=instance.on_text_focus)
            t.focus = True
            instance.screen.polestar = ref(instance)
        super(Editable, self).on_state(instance, value)

    def on_text_validate(self, instance, value):
        if not value: #if instance.text == ""
            instance.focus = False
            return False
        else:
            value = value.lstrip()
            self.text = value
            #self.text = unicode(value, encoding=chardetect(value)["encoding"])
            instance.focus = False
            return True

    def on_text_focus(self, instance, focus):
        if focus is False:
            self.state = 'normal'
        
    def cancel(self):
        Clock.unschedule(self._double_tap_interval)
        self._double_tap_time = 0.0
        self._switch = False
        super(Editable, self).cancel()

class DoubleClickable(Editable):
    double_click_switch = BooleanProperty(False)

    def on_state(self, instance, value):
        instance._switch = False

        if value == 'edit':
            self.double_click_switch = not self.double_click_switch
            instance.state = 'normal'

class DropAnimation(Animation):
    indices = ListProperty(None)

class DragNDroppable(ButtonRoot):
    state = OptionProperty('normal', options=('normal', 'down', 'dragged'))
    hold_time = NumericProperty(0.0)
    drop_zones = ListProperty([])#ListProperty(WeakList())
    
    def __init__(self, **kwargs):
        self.register_event_type('on_drag')
        self.register_event_type('on_drop')
        super(DragNDroppable, self).__init__(**kwargs)

    def on_hold_down(self, dt):
        if ((self.state == 'down') and not self.disabled):
            self.hold_time += dt

            if self.hold_time > 0.85:
                self.state = 'dragged'

        else:
            self.hold_time = 0.0
            return False

    def on_state(self, instance, value):
        listview = instance.listview

        if ((value <> 'dragged') and listview.placeholder):
            listview.placeholder = None
            listview.parent.polestar = lambda : None
        elif value == 'dragged':
            listview.deparent(instance)
            listview.parent.polestar = ref(instance)
        super(DragNDroppable, self).on_state(instance, value)

    def on_touch_down(self, touch):
        """if self.state == 'dragged':
            touch.ungrab(self)
            return True"""
        if self.state == 'normal':
            sup = super(ButtonRoot, self).on_touch_down(touch)

            if not sup:
                touch.ud['indices'] = WeakKeyDictionary()
            else:
                return sup

        return super(DragNDroppable, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'dragged':
                self.dispatch('on_drag', self, touch.y)

                for zone in self.drop_zones:
                    if self.collide_widget(zone):
                        touch.ud['indices'] = zone.dispatch('on_drag', self, touch.ud['indices'])
                return True

        return super(DragNDroppable, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        #super(ButtonRoot, self).on_touch_up(touch)

        if touch.grab_current is self:
            assert(self in touch.ud)

            if self.state == 'dragged':
                touch.ungrab(self)
                indices = touch.ud['indices']

                for viewer in self.drop_zones:
                    if viewer.collide_point(*self.center):
                        break
                else:
                    viewer = None

                self.dispatch('on_drop', self, viewer, indices)
                return True

        return super(DragNDroppable, self).on_touch_up(touch)

    def on_drag(self, instance, pos_y):
        instance.center_y = pos_y
        
    def on_drop(self, instance, viewer, indices):
        point = instance.center

        if viewer:
            child = viewer.placeholder

            if not child:
                for child in viewer.container.children:
                    if child.collide_point(*point):
                        break

            _anim = DropAnimation(y=child.y, d=0.1)

        else:
            viewer = instance.listview
            child = viewer.placeholder
            _anim = DropAnimation(y=child.y, d=0.5, t='out_back')

        def _on_start(a, w):
            a.indices = viewer.dispatch('on_motion_out', w, indices)

        def _on_complete(a, w):
            viewer.reparent(w, child, a.indices)

        _anim.bind(on_start=_on_start, on_complete=_on_complete)
        instance._anim = ref(_anim)
        instance._anim().start(instance)

    def cancel(self):
        Clock.unschedule(self.on_hold_down)
        self.hold_time = 0.0
        super(DragNDroppable, self).cancel()

class Button_(Clickable):
    state = OptionProperty('normal', options=('down', 'normal'))

    def __init__(self, **kwargs):
        super(Button_, self).__init__(**kwargs)
        self._press_ = Clock.create_trigger(self._trigger_press, 0)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(Button_, self).on_touch_down(touch)

class DeleteButton(Button_):
    button = ObjectProperty(None, allownone=True)

    def on_press(self):
        self.button.screen.dispatch('on_delete', self.button)

class CompleteButton(DeleteButton):

    def on_press(self):
        self.button.screen.dispatch('on_complete', self.button)

class EditButton(Editable):
    
    def on_touch_down(self, touch):
        if ((self.collide_point(*touch.pos)) or (self.state == 'edit')):
            return super(EditButton, self).on_touch_down(touch)

    def on_text_validate(self, instance):
        if super(EditButton, self).on_text_validate(instance, instance.text):
            self.parent.dispatch('on_comments', instance.text)

class DoubleClickButton(DoubleClickable):
    icon_text = StringProperty('')
    icon_font_name = StringProperty('heydings_icons.ttf')

    def on_touch_down(self, touch):
        if ((self.collide_point(*touch.pos)) and (self.state == 'normal')):
            return super(DoubleClickButton, self).on_touch_down(touch)

class AccordionListItem(Selectable, StencilLayout):
    title = ObjectProperty(None)
    content = ObjectProperty(None)
    listview = ObjectProperty(None)
    shadow_color = ListProperty([])
    state_color = ListProperty([])
    text_color = ListProperty([])
    text = StringProperty('')
    collapse_alpha = NumericProperty(1.0)
    title_height_hint = NumericProperty(0.0)
    content_height_hint = NumericProperty(0.0)

    def _get_height(self):
        if self.title and self.content:
            return self.title.height + (self.content.height*(1-self.collapse_alpha))
        else:
            return 1

    height = AliasProperty(_get_height, None, bind=('center_y', 'top', 'title', 'content', 'collapse_alpha'))

    def _get_state(self):
        if self.title:
            return self.title.state

    def _set_state(self, state):
        if (self.title and (self.title.state <> state)):
            self.title.state = state
        else:
            return False

    state = AliasProperty(_get_state, _set_state, bind=('title',))

    def __init__(self, **kwargs):
        self._anim = lambda : None
        super(AccordionListItem, self).__init__(**kwargs)

    def _do_select(self, alpha):
        """if self._anim():
            self._anim().stop()
            self._anim = None"""

        _anim = Animation(collapse_alpha=alpha, t='out_expo', d=0.25)
        _anim.bind(on_progress=self._do_progress)
        self._anim = ref(_anim)
        _anim.start(self)

    def _do_progress(self, anim, instance, progression):
        instance.listview._sizes[instance.index] = instance.height

    def select(self, *args):
        self._do_select(0.0)

    def deselect(self, *args):
        self._do_select(1.0)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        elif self.disabled:
            return True
        elif self._anim() is not None:
            return True
        else:
            return super(AccordionListItem, self).on_touch_down(touch)

class FreeRotateLayout(Widget):
    content = ObjectProperty(None)
    transform = ObjectProperty(Matrix())
    transform_inv = ObjectProperty(Matrix())

    def __init__(self, **kwargs):
        self.register_event_type('on_change')
        self.register_event_type('on_release')
        super(FreeRotateLayout, self).__init__(**kwargs)

    def to_parent(self, x, y, **k):
        p = self.transform.transform_point(x, y, 0)
        return (p[0], p[1])

    def to_local(self, x, y, **k):
        p = self.transform_inv.transform_point(x, y, 0)
        return (p[0], p[1])

    def apply_transform(self, trans, post_multiply=False, anchor=(0, 0), matrix=Matrix):
        t = matrix().translate(anchor[0], anchor[1], 0)
        t = t.multiply(trans)
        t = t.multiply(matrix().translate(-anchor[0], -anchor[1], 0))

        if post_multiply:
            self.transform = self.transform.multiply(t)
        else:
            self.transform = t.multiply(self.transform)

    def _get_bbox(self):
        xmin, ymin = xmax, ymax = self.to_parent(0, 0)

        for point in [(self.width, 0), (0, self.height), self.size]:
            x, y = self.to_parent(*point)

            if x < xmin:
                xmin = x
            if y < ymin:
                ymin = y
            if x > xmax:
                xmax = x
            if y > ymax:
                ymax = y

        return (xmin, ymin), (xmax - xmin, ymax - ymin)

    bbox = AliasProperty(_get_bbox, None, bind=('width', 'height'))

    def _get_angle(self, vector=Vector):
        v1 = vector(0, 10)
        tp = self.to_parent
        v2 = vector(*tp(*self.pos)) - tp(self.x, self.y + 10)
        ret = -1.0 * (v1.angle(v2) + 180) % 360
        return ret

    def _set_angle(self, angle, matrix=Matrix):#, radians=math.radians, ceil=math.ceil):
        angle_change = self.angle - angle
        r = matrix().rotate(-radians(angle_change), 0, 0, 1)
        self.apply_transform(r, post_multiply=True, anchor=self.to_local(*self.center))

    angle = AliasProperty(_get_angle, _set_angle, bind=('x', 'y'))

    def _get_center(self):
        bbox = self.bbox
        return (bbox[0][0] + bbox[1][0] / 2.0,
                bbox[0][1] + bbox[1][1] / 2.0)

    def _set_center(self, center, vector=Vector, matrix=Matrix):
        if center <> self.center:
            t = vector(*center) - self.center
            trans = matrix().translate(t.x, t.y, 0)
            self.apply_transform(trans)
        else:
            return False

    center = AliasProperty(_get_center, _set_center, bind=('bbox', ))

    def _get_pos(self):
        return self.bbox[0]

    def _set_pos(self, pos, vector=Vector, matrix=Matrix):
        _pos = self.bbox[0]

        if pos <> _pos:
            t = vector(*pos) - _pos
            trans = matrix().translate(t.x, t.y, 0)
            self.apply_transform(trans)
        else:
            return False

    pos = AliasProperty(_get_pos, _set_pos, bind=('bbox', ))

    def _get_x(self):
        return self.bbox[0][0]

    def _set_x(self, x):
        if x == self.bbox[0][0]:
            return False
        self.pos = (x, self.y)
        return True

    x = AliasProperty(_get_x, _set_x, bind=('bbox', ))

    def _get_y(self):
        return self.bbox[0][1]

    def _set_y(self, y):
        if y == self.bbox[0][1]:
            return False
        self.pos = (self.x, y)
        return True

    y = AliasProperty(_get_y, _set_y, bind=('bbox', ))

    def get_right(self):
        return self.x + self.bbox[1][0]

    def set_right(self, value):
        self.x = value - self.bbox[1][0]

    right = AliasProperty(get_right, set_right, bind=('x', 'width'))

    def get_top(self):
        return self.y + self.bbox[1][1]

    def set_top(self, value):
        self.y = value - self.bbox[1][1]

    top = AliasProperty(get_top, set_top, bind=('y', 'height'))

    def get_center_x(self):
        return self.x + self.bbox[1][0] / 2.

    def set_center_x(self, value):
        self.x = value - self.bbox[1][0] / 2.

    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'width'))

    def get_center_y(self):
        return self.y + self.bbox[1][1] / 2.

    def set_center_y(self, value):
        self.y = value - self.bbox[1][1] / 2.

    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'height'))

    def add_widget(self, *args):
        if self.content:
            self.content.add_widget(*args)
        else:
            super(FreeRotateLayout, self).add_widget(*args)

    def remove_widget(self, *args):
        if self.content:
            self.content.remove_widget(*args)
        else:
            super(FreeRotateLayout, self).remove_widget(*args)

    def clear_widgets(self):
        self.content.clear_widgets()

    def on_transform(self, instance, value):
        instance.transform_inv = value.inverse()

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return 0 <= x <= self.width and 0 <= y <= self.height

    def on_release(self, *args):
        pass

    def on_change(self, *args):
        pass


Builder.load_string("""
#:import BoxLayout parents.BoxLayout

<NavBar>:
    size_hint: 1, 0.1127
    pos_hint:{'top': 1, 'x': 0}
    canvas.before:
        Color:
            rgba: app.dark_blue
        Rectangle:
            size: self.size
            pos: self.pos

    Label:
        text: root.text
        opacity: 0.5
        shorten: root.shorten
        font_size: root.font_size
        font_name: 'Walkway Bold.ttf'
        color: app.white
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
    StatusBar:
        size_hint: 1, 0.3125
        pos_hint: {'x': 0, 'top': 1}

<ButtonRoot>:
    label: label_id
    layout: layout_id

    FloatLayout:
        id: layout_id
        size: root.size
        pos: root.pos
        canvas.before:
            Color:
                rgba: root.state_color
            Rectangle:
                size: self.size
                pos: self.pos

        Label:
            id: label_id
            text: root.text
            size_hint: 1, 1
            pos_hint: {'x': 0, 'y': 0}
            font_size: root.font_size
            font_name: root.font_name
            shorten: root.shorten
            color: root.text_color
            markup: root.markup
            disabled_color: self.color
            text_size: (self.size[0]-(0.1*self.size[0]), None) if root.aleft else (None, None)

<Button_>:
    state_color: app.blue
    text_color: app.white
    font_size: self.height*0.421875

<DeleteButton>:
    text: 'X'
    width: self.height
    font_name: 'heydings_icons.ttf'
    font_size: self.height*0.7
    state_color: app.red
    text_color: app.purple                                                                 
    canvas.before:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.top-1, self.right, self.top-1
            width: 1.0

<CompleteButton>:
    text: 'O'
    state_color: app.purple
    text_color: app.white

<-EditButton>:
    label: label_id

    Label:
        id: label_id
        pos: root.pos
        text: root.text
        size: root.size
        font_size: root.font_size
        font_name: root.font_name
        shorten: root.shorten
        color: root.text_color
        disabled_color: self.color
        markup: root.markup
        text_size: self.size
        valign: 'top'

<-DoubleClickButton>:
    label: label_id

    Label:
        id: icon_id
        text: root.icon_text
        size_hint: None, None
        height: root.height
        width: self.height
        pos: root.pos
        color: root.text_color
        disabled_color: self.color
        font_name: root.icon_font_name
        font_size: root.font_size
        text_size: self.size[0], None
    Label:
        id: label_id
        text: root.text
        size_hint: None, None
        height: root.height
        width: root.width - icon_id.width
        pos: icon_id.right, root.pos[1]
        color: root.text_color
        disabled_color: self.color
        font_name: 'Walkway Bold.ttf'
        font_size: root.font_size
        text_size: self.size[0], None

<StencilLayout>:
    canvas.before:
        StencilPush
        Rectangle:
            pos: self.pos
            size: self.size
        StencilUse
    canvas.after:
        StencilUnUse
        Rectangle:
            pos: self.pos
            size: self.size
        StencilPop

<AccordionListItem>:
    size_hint: 1, None
    shadow_color: app.shadow_gray

<-BoundedTextInput>:
    font_name: 'Walkway Bold.ttf'
    active_color: app.white
    inactive_color: app.smoke_white
    foreground_color: app.dark_blue
    disabled: self.disabled
    canvas.before:
        Color:
            rgba: self.active_color if self.focus else self.inactive_color
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: (1, 0, 0, 1 if self.focus and not self.cursor_blink else 0)
        Rectangle:
            pos: [int(x) for x in self.cursor_pos]
            size: 1, -self.line_height
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text and not self.focus else self.foreground_color)

<FreeRotateLayout>:
    content: content_id
    canvas.before:
        PushMatrix
        MatrixInstruction:
            matrix: self.transform
    canvas.after:
        PopMatrix

    FloatLayout:
        id: content_id
        size: root.size

<NewItemWidget>:
    state: 'edit' if textinput_id.focus else 'normal'
    canvas.before:
        Color:
            rgba: app.dark_blue
        Rectangle:
            size: self.size
            pos: self.pos

    BoxLayout:
        spacing: 14
        size_hint: 0.9781, 0.7561
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

        BoundedTextInput:
            id: textinput_id
            size_hint: 0.774, 1
            font_size: self.width*0.06
            hint_text: root.hint_text
            multiline: False
            on_text_validate: root.dispatch('on_text_validate', args[0], args[0].text)
        Button_:
            size_hint: 0.226, 1
            text: 'Add'
            on_press: root.dispatch('on_text_validate', textinput_id, textinput_id.text)


<Screen_>:
    keyboard_height: 432

""")
