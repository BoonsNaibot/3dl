from weakref import ref
from kivy.clock import Clock
from kivy.lang import Builder
from uiux import StencilLayout
from kivy.animation import Animation
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import AliasProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty

class ScrollerEffect(DampedScrollEffect):
    min_velocity = NumericProperty(10)
    _parent = ObjectProperty(None)
    
    def _get_target_widget(self):
        if self._parent:
            return self._parent._viewport()

    target_widget = AliasProperty(_get_target_widget, None, bind=('_parent',))

    def _get_max(self):
        return self._parent.y

    max = AliasProperty(_get_max, None, bind=('_parent',))

    def _get_min(self):
        tw = self.target_widget

        if tw:
            #return -(tw.size[1] - tw.parent.height)
            return self._parent.top - tw.height
        else:
            return 0

    min = AliasProperty(_get_min, None, bind=('_parent', 'target_widget'))
    
    def on_scroll(self, instance, value):
        vp = instance.target_widget

        if vp:
            parent = instance._parent
            sh = vp.height - parent.height

            if sh >= 1:
                vp.y = value
                sy = value/float(sh)
                parent.scroll_y = -sy
            else:
                vp.top = parent.top
                parent.scroll_y = 1.0
            if ((not instance.is_manual) and ((abs(instance.velocity) <= instance.min_velocity) or (not value))):
                instance._parent.mode = 'normal'

    def cancel(self):
        self.is_manual = False
        self.velocity = 0
        self._parent.mode = 'normal'

class Scroller(StencilLayout):
    scroll_distance = NumericProperty('10dp')
    scroll_y = NumericProperty(1.0)
    bar_color = ListProperty([0.7, 0.7, 0.7, 0.9])
    bar_width = NumericProperty('2dp')
    bar_margin = NumericProperty(0)
    effect_y = ObjectProperty(None)
    _viewport = ObjectProperty(lambda : None)
    bar_alpha = NumericProperty(1.0)
    mode = OptionProperty('normal', options=('down', 'normal', 'scrolling'))

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / Scroller size %
        ret = (0, 1.0)

        if self._viewport():
            vh = self._viewport().height
            h = self.height

            if vh > h:
                ph = max(0.01, h / float(vh))
                sy = min(1.0, max(0.0, self.scroll_y))
                py = (1. - ph) * sy
                ret = (py, ph)

        return ret

    vbar = AliasProperty(_get_vbar, None, bind=('scroll_y', '_viewport'))

    def __init__(self, **kwargs):
        self.effect_y = ScrollerEffect(_parent=self.proxy_ref, round_value=False)
        super(Scroller, self).__init__(**kwargs)

    def do_layout(self, *args, **kwargs):
        if 1 not in self.size:
            vp = self._viewport()

            if vp:
                # Just like papa
                w, h = kwargs.get('size', self.size)
                x, y = kwargs.get('pos', self.pos)
                #vp.w, vp.x = w, x

                if not (self.effect_y.min <= self.effect_y.value <= self.effect_y.max):
                    self.effect_y.value = self.effect_y.min * self.scroll_y
                if vp.height > h:
                    sh = vp.height - h
                    vp.y = y - self.scroll_y * sh
                else:
                    vp.top = y + h

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.effect_y.start(touch.y)

            if self.mode == 'normal':
                self.mode = 'down'
                touch.push()
                touch.apply_transform_2d(self.to_widget)
                touch.apply_transform_2d(self.to_parent)
                ret = super(Scroller, self).on_touch_down(touch)
                touch.pop()
                return ret
            elif self.mode == 'scrolling':
                return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            
            if self.mode == 'down':
                touch.push()
                touch.apply_transform_2d(self.to_widget)
                touch.apply_transform_2d(self.to_parent)
                ret = super(Scroller, self).on_touch_move(touch)
                touch.pop()
                
                if ret:
                    touch.ungrab(self)
                    self.effect_y.cancel()
                    return True
                elif ((abs(touch.dy) > self.scroll_distance) and (self._viewport().height > self.height)):
                    self.mode = 'scrolling'
                    l = len(touch.grab_list)
    
                    if l > 1:
                        for x in xrange(l):
                            item = touch.grab_list[x]()
    
                            if type(item) is not Scroller:
                                touch.ungrab(item)
                                item.cancel()

            elif self.mode == 'scrolling':
                self.effect_y.update(touch.y)

            return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            effect = self.effect_y

            if self.mode == 'down':
                effect.cancel()
            elif self.mode == 'scrolling':
                effect.stop(touch.y)
                effect.on_scroll(effect, effect.scroll)
            return True

        touch.push()
        touch.apply_transform_2d(self.to_widget)
        touch.apply_transform_2d(self.to_parent)
        ret = super(Scroller, self).on_touch_up(touch)
        touch.pop() 
        return ret

    def update_from_scroll(self, *largs):
        Clock.schedule_once(self._start_decrease_alpha, .5)

    def _start_decrease_alpha(self, *l):
        self.bar_alpha = 1.
        Animation(bar_alpha=0., d=.5, t='out_quart').start(self)

    def add_widget(self, widget, index=0):
        if self._viewport():
            raise Exception('Scroller accept only one widget')
        super(Scroller, self).add_widget(widget, index)
        self._viewport = ref(widget)
        widget.unbind(pos=self._trigger_layout,
                      pos_hint=self._trigger_layout)

    def remove_widget(self, widget):
        super(Scroller, self).remove_widget(widget)
        if widget is self._viewport():
            self._viewport = lambda : None

Builder.load_string("""
<Scroller>:
    canvas.after:
        Color:
            rgba: self.bar_color[:3] + [self.bar_color[3] * self.bar_alpha]
        Rectangle:
            pos: self.right - self.bar_width - self.bar_margin, self.y + self.height * self.vbar[0]
            size: self.bar_width, self.height * self.vbar[1]
""")
