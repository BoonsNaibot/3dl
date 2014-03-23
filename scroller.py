from kivy.clock import Clock
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import AliasProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty

class ScrollerEffect(DampedScrollEffect):
    _parent = ObjectProperty(None)
    max = NumericProperty(0)
    
    def _get_target_widget(self):
        return self._parent._viewport
        
    target_widget = AliasProperty(_get_target_widget, None, bind=('_parent',))
    
    def _get_min(self):
        tw = self.target_widget

        if tw:
            return -(tw.size[1] - self._parent.height)
        else:
            return 0
        
    min = AliasProperty(_get_min, None, bind=('target_widget',))
    
    def on_scroll(self, instance, value):
        parent = instance._parent
        vp = instance.target_widget
        
        if vp:
            sh = vp.height - parent.height
            
            if sh >= 1:
                sy = value/float(sh)
                parent.scroll_y = -sy
                parent._trigger_update_from_scroll()
                
    def on_is_manual(self, instance, value):
        if not value:

            def _mode_change(*_):
                if not instance.is_manual:
                    instance._parent.mode = 'normal'
                else:
                    return False
            Clock.schedule_once(_mode_change, 0.055)


class Scroller(StencilView):
    scroll_distance = NumericProperty('20dp')
    scroll_y = NumericProperty(1.)
    bar_color = ListProperty([.7, .7, .7, .9])
    bar_width = NumericProperty('2dp')
    bar_margin = NumericProperty(0)
    bar_anim = ObjectProperty(None, allownone=True)
    effect_y = ObjectProperty(None, allownone=True)
    _viewport = ObjectProperty(None, allownone=True)
    bar_alpha = NumericProperty(1.)
    mode = OptionProperty('normal', options=('normal', 'scrolling'))

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
            
            if self.mode == 'scrolling':
                self.effect_y.cancel()
            else:
                touch.ud['touch_down'] = touch

            self.effect_y.start(touch.y)
            return True

    def on_touch_move(self, touch):
        # Take advantage of the fact that, given the imprecision of 'finger-touching',
        # the nature of mobile devices is such that an `on_touch_down` event basically 
        # guarantees an `on_touch_move` event.

        if 'touch_down' in touch.ud:
            _touch = touch.ud.pop('touch_down')
            
            if (abs(touch.dy) < self.scroll_distance):
                self.effect_y.cancel()
                
                if self.mode <> 'scrolling':
                    touch.ungrab(self)
                    _touch.push()
                    _touch.apply_transform_2d(self.to_widget)
                    _touch.apply_transform_2d(self.to_parent)
                    super(Scroller, self).on_touch_down(_touch)
                    _touch.pop()
                    touch = _touch

            elif self.mode <> 'scrolling':
                self.mode = 'scrolling'
            del _touch

        elif ((touch.grab_current is self) and (self.mode == 'scrolling')):
            min_height = self._viewport.height

            if min_height > self.height:
                self.effect_y.update(touch.y)
                return True

        return super(Scroller, self).on_touch_move(touch)

    def on_touch_up(self, touch):

        if touch.grab_current is self:
            touch.ungrab(self)
            self.effect_y.stop(touch.y)

        return super(Scroller, self).on_touch_up(touch)

    """def _do_touch_up(self, touch, *largs):
        super(Scroller, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in xrange(len(touch.grab_list)):
            x = touch.grab_list.pop()
            x = x()

            if x:
                touch.grab_current = x
                super(Scroller, self).on_touch_up(touch)
        touch.grab_current = None"""

    def convert_distance_to_scroll(self, dx, dy):
        '''Convert a distance in pixels to a scroll distance, depending on the
        content size and the Scroller size.

        The result will be a tuple of scroll distance that can be added to
        :data:`scroll_x` and :data:`scroll_y`
        '''
        sx, sy = (0, 0)

        if self._viewport:
            vp = self._viewport

            if vp.width > self.width:
                sw = vp.width - self.width
                sx = dx / float(sw)
            else:
                sx = 0
            if vp.height > self.height:
                sh = vp.height - self.height
                sy = dy / float(sh)
            else:
                sy = 1

        return sx, sy

    def update_from_scroll(self, *largs):
        '''Force the reposition of the content, according to current value of
        :data:`scroll_x` and :data:`scroll_y`.

        This method is automatically called when one of the :data:`scroll_x`,
        :data:`scroll_y`, :data:`pos` or :data:`size` properties change, or
        if the size of the content changes.
        '''
        vp = self._viewport

        if vp:
            
            if vp.size_hint_x is not None:
                vp.width = vp.size_hint_x * self.width
            if vp.width > self.width:
                sw = vp.width - self.width
                x = self.x - self.scroll_x * sw
            else:
                x = self.x
            if vp.height > self.height:
                sh = vp.height - self.height
                y = self.y - self.scroll_y * sh
            else:
                y = self.top - vp.height
            vp.pos = x, y

            # new in 1.2.0, show bar when scrolling happen
            # and slowly remove them when no scroll is happening.
            self.bar_alpha = 1.
            
            if self.bar_anim:
                self.bar_anim.stop()
                Clock.unschedule(self._start_decrease_alpha)
    
            Clock.schedule_once(self._start_decrease_alpha, .5)

    def _start_decrease_alpha(self, *l):
        self.bar_alpha = 1.
        Animation(bar_alpha=0., d=.5, t='out_quart').start(self)

    #
    # Private
    #
    def add_widget(self, widget, index=0):
        if self._viewport:
            raise Exception('Scroller accept only one widget')
        super(Scroller, self).add_widget(widget, index)
        self._viewport = widget
        widget.bind(size=self._trigger_update_from_scroll,
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
