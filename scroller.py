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
            return self._parent._viewport.proxy_ref

    target_widget = AliasProperty(_get_target_widget, None)
    
    def _get_min(self):
        tw = self.target_widget

        if tw:
            #return -(tw.size[1] - tw.parent.height)
            return tw.parent.top - tw.size[1]
        else:
            return 0
        
    min = AliasProperty(_get_min, None)
    
    def _get_max(self):
        return self._parent.pos[1]
        
    max = AliasProperty(_get_max, None)
    
    def on_scroll(self, instance, value):
        vp = instance.target_widget

        if vp:
            parent = vp.parent
            sh = vp.height - parent.height

            if sh >= 1:
                vp.y = value
                sy = value/float(sh)
                parent.scroll_y = -sy
            else:
                vp.top = parent.top

            if ((not instance.is_manual) and ((abs(instance.velocity) <= instance.min_velocity) or (not value))):
                parent.mode = 'normal'
                
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
    _viewport = ObjectProperty(None)
    bar_alpha = NumericProperty(1.0)
    mode = OptionProperty('normal', options=('down', 'normal', 'scrolling'))

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / Scroller size %
        ret = (0, 1.0)

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
        self.bind(scroll_y=self._trigger_update_from_scroll)

    def do_layout(self, *args, **kwargs):
        super(Scroller, self).do_layout(*args, **kwargs)
        self._trigger_update_from_scroll()

    def on_pos(self, *args):
        if self._viewport:
            vp = self._viewport

            if vp.height > self.height:
                sh = vp.height - self.height
                vp.y = self.y - self.scroll_y * sh
            else:
                vp.top = self.top

    def on_height(self, *args):
        if self._viewport:
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
                    self.effect_y.cancel()
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
            elif self.mode == 'scrolling':
                effect.stop(touch.y)
                effect.on_scroll(effect, effect.scroll)
            return True

        return super(Scroller, self).on_touch_up(touch)

    def update_from_scroll(self, *largs):
        """p = self._viewport

        if vp:
            vp.width = vp.size_hint_x * self.width
            vp.x = self.x

            if vp.height > self.height:
                vp.y = self.effect_y.value
                sh = vp.height - self.height
                y = self.y - self.scroll_y * sh
            else:
                y = self.top - vp.height
            vp.pos = self.x, y"""
        Clock.schedule_once(self._start_decrease_alpha, .5)

    def _start_decrease_alpha(self, *l):
        self.bar_alpha = 1.
        Animation(bar_alpha=0., d=.5, t='out_quart').start(self)

    def add_widget(self, widget, index=0):
        if self._viewport:
            raise Exception('Scroller accept only one widget')
        super(Scroller, self).add_widget(widget, index)
        self._viewport = widget
        widget.bind(height=self.on_height)

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
