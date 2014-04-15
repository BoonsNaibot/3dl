from kivy.clock import Clock
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import AliasProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty

class ScrollerEffect(DampedScrollEffect):
    min_velocity = NumericProperty(2.5)
    _parent = ObjectProperty(None)
    max = NumericProperty(0)
    
    def _get_target_widget(self):
        if self._parent:
            return self._parent._viewport.proxy_ref

    target_widget = AliasProperty(_get_target_widget, None)
    
    def _get_min(self):
        parent = self._parent
        tw = parent._viewport

        if tw:
            return -(tw.size[1] - parent.height)
        else:
            return 0
        
    min = AliasProperty(_get_min, None)
    
    def on_scroll(self, instance, value):
        parent = instance._parent
        vp = parent._viewport

        if vp:
            sh = vp.height - parent.height

            if sh >= 1:
                sy = value/float(sh)
                
                if parent.scroll_y == -sy:
                    parent._trigger_update_from_scroll()
                else:
                    parent.scroll_y = -sy

            if ((not instance.is_manual) and ((abs(instance.velocity) <= instance.min_velocity) or (not value))):
                parent.mode = 'normal'
                """def _mode_change(*_):
                    if ((not instance.is_manual) and ((abs(instance.velocity) <= instance.min_velocity) or (not instance.scroll))):
                        parent.mode = 'normal'
                    else:
                        return False
                Clock.schedule_once(_mode_change, 0.055)"""

class Scroller(StencilView):
    scroll_distance = NumericProperty('10dp')
    scroll_y = NumericProperty(1.)
    bar_color = ListProperty([.7, .7, .7, .9])
    bar_width = NumericProperty('2dp')
    bar_margin = NumericProperty(0)
    bar_anim = ObjectProperty(None, allownone=True)
    effect_y = ObjectProperty(None)
    _viewport = ObjectProperty(None)
    bar_alpha = NumericProperty(1.0)
    mode = OptionProperty('normal', options=('down', 'normal', 'scrolling'))

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / Scroller size %
        ret = (0, 1.)

        if self._viewport:
            vh = self._viewport.height
            h = self.height
            
            if vh > h:
                ph = max(0.01, h / float(vh))
                sy = min(1.0, max(0.0, self.scroll_y))
                py = (1. - ph) * sy
                ret = (py, ph)

        return ret

    vbar = AliasProperty(_get_vbar, None, bind=('scroll_y', '_viewport'))

    def __init__(self, **kwargs):
        self._trigger_update_from_scroll = Clock.create_trigger(self.update_from_scroll, -1)
        super(Scroller, self).__init__(**kwargs)

        self.effect_y = ScrollerEffect(_parent=self)
        self.bind(scroll_y=self._trigger_update_from_scroll,
                  pos=self._trigger_update_from_scroll,
                  size=self._trigger_update_from_scroll)
                  
    def on_height(self, instance, *args):
        self.effect_y.value = self.effect_y.min * self.scroll_y

    def on_touch_down(self, touch):        
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.effect_y.start(touch.y)

            if self.mode == 'normal':
                self.mode = 'down'
                return super(Scroller, self).on_touch_down(touch)
            elif self.mode == 'scrolling':
                return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            
            if self.mode == 'down':
                ret = super(Scroller, self).on_touch_move(touch)
                
                if ret:
                    touch.ungrab(self)
                    self.halt()
                    return True
                elif ((abs(touch.dy) > self.scroll_distance) and (self._viewport.height > self.height)):
                    self.mode = 'scrolling'
                    grab_list = touch.grab_list
                    l = len(grab_list)
    
                    if l > 1:
                        for x in xrange(l):
                            item = grab_list[x]()
    
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
                self.mode = 'normal'
            elif self.mode == 'scrolling':
                effect.stop(touch.y)
            effect.on_scroll(effect, effect.scroll)
            return True

        return super(Scroller, self).on_touch_up(touch)

    def update_from_scroll(self, *largs):
        vp = self._viewport

        if vp:
            vp.width = vp.size_hint_x * self.width

            if vp.height > self.height:
                sh = vp.height - self.height
                y = self.y - self.scroll_y * sh
            else:
                y = self.top - vp.height
            vp.pos = self.x, y
            self.bar_alpha = 1.
            
            if self.bar_anim:
                self.bar_anim.stop()
                Clock.unschedule(self._start_decrease_alpha)
            Clock.schedule_once(self._start_decrease_alpha, .5)

    def halt(self):        
        self.effect_y.is_manual = False
        self.on_height(self)
        self.effect_y.velocity = 0
        self.mode = 'normal'

    def _start_decrease_alpha(self, *l):
        self.bar_alpha = 1.
        Animation(bar_alpha=0., d=.5, t='out_quart').start(self)

    def add_widget(self, widget, index=0):
        if self._viewport:
            raise Exception('Scroller accept only one widget')
        super(Scroller, self).add_widget(widget, index)
        self._viewport = widget
        widget.bind(#size=self._trigger_update_from_scroll,
                    height=self.on_height)
        self._trigger_update_from_scroll()

    def remove_widget(self, widget):
        super(Scroller, self).remove_widget(widget)
        if widget is self._viewport:
            self._viewport = None

Builder.load_string("""
<Scroller>:
    canvas.after:
        Color:
            rgba: self.bar_color[:3] + [self.bar_color[3] * self.bar_alpha]
        Rectangle:
            pos: self.right - self.bar_width - self.bar_margin, self.y + self.height * self.vbar[0]
            size: self.bar_width, self.height * self.vbar[1]
""")
