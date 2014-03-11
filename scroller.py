from functools import partial
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import NumericProperty, BooleanProperty, AliasProperty, ObjectProperty, ListProperty, OptionProperty

class ScrollerEffect(DampedScrollEffect):
    _parent = ObjectProperty(None)
    max = NumericProperty(0)
    
    def _get_target_widget(self):
        return self._parent._viewport
        
    target_widget = AliasProperty(_get_target_widget, None, bind=('_parent',))
    
    def _get_min(self):
        return -(self.target_widget.size[1] - self._parent.height)
        
    min = AliasProperty(_get_min, None, bind=('target_widget',))
    
    def _get_value(self):
        return self.min * self._parent.scroll_y

    value = AliasProperty(_get_value, None, bind=('min', '_parent'))
    
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
            instance._parent.mode = 'normal'


class Scroller(StencilView):
    '''Scroller class. See module documentation for more information.

    .. versionchanged:: 1.7.0

        `auto_scroll`, `scroll_friction`, `scroll_moves`, `scroll_stoptime' has
        been deprecated, use :data:`effect_cls` instead.
    '''

    scroll_distance = NumericProperty(7)
    '''Distance to move before scrolling the :class:`Scroller`, in pixels. As
    soon as the distance has been traveled, the :class:`Scroller` will start
    to scroll, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :data:`scroll_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 20 (pixels), according to the default value in user
    configuration.
    '''

    scroll_y = NumericProperty(1.)
    '''Y scrolling value, between 0 and 1. If 0, the content's bottom side will
    touch the bottom side of the Scroller. If 1, the content's top side will
    touch the top side.

    This property is controled by :class:`Scroller` only if
    :data:`do_scroll_y` is True.

    :data:`scroll_y` is a :class:`~kivy.properties.NumericProperty`,
    default to 1.
    '''

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / Scroller size %
        if self._viewport is None:
            return 0, 1.
        vh = self._viewport.height
        h = self.height
        if vh < h or vh == 0:
            return 0, 1.
        ph = max(0.01, h / float(vh))
        sy = min(1.0, max(0.0, self.scroll_y))
        py = (1. - ph) * sy
        return (py, ph)

    vbar = AliasProperty(_get_vbar, None, bind=(
        'scroll_y', '_viewport', 'viewport_size'))
    '''Return a tuple of (position, size) of the vertical scrolling bar.

    .. versionadded:: 1.2.0

    The position and size are normalized between 0-1, and represent a
    percentage of the current Scroller height. This property is used
    internally for drawing the little vertical bar when you're scrolling.

    :data:`vbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
    '''

    bar_color = ListProperty([.7, .7, .7, .9])
    '''Color of horizontal / vertical scroll bar, in RGBA format.

    .. versionadded:: 1.2.0

    :data:`bar_color` is a :class:`~kivy.properties.ListProperty`, default to
    [.7, .7, .7, .9].
    '''

    bar_width = NumericProperty('2dp')
    '''Width of the horizontal / vertical scroll bar. The width is interpreted
    as a height for the horizontal bar.

    .. versionadded:: 1.2.0

    :data:`bar_width` is a :class:`~kivy.properties.NumericProperty`, default
    to 2
    '''

    bar_margin = NumericProperty(0)
    '''Margin between the bottom / right side of the Scroller when drawing
    the horizontal / vertical scroll bar.

    .. versionadded:: 1.2.0

    :data:`bar_margin` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    effect_y = ObjectProperty(None, allownone=True)
    '''Effect to apply for the Y axis. If None is set, an instance of
    :data:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :data:`effect_y` is a :class:`~kivy.properties.ObjectProperty`, default to
    None, read-only.
    '''

    viewport_size = ListProperty([0, 0])
    '''(internal) Size of the internal viewport. This is the size of your only
    child in the Scroller.
    '''

    # private, for internal use only

    _viewport = ObjectProperty(None, allownone=True)
    bar_alpha = NumericProperty(1.)

    def __init__(self, **kwargs):
        self._trigger_update_from_scroll = Clock.create_trigger(self.update_from_scroll, -1)
        super(Scroller, self).__init__(**kwargs)

        self.effect_y = ScrollerEffect(_parent=self)
        self.bind(
            width=self._update_effect_x_bounds,
            height=self._update_effect_y_bounds,
            viewport_size=self._update_effect_bounds,
            _viewport=self._update_effect_widget,
            scroll_y=self._trigger_update_from_scroll,
            pos=self._trigger_update_from_scroll,
            size=self._trigger_update_from_scroll)

    def on_touch_down(self, touch):
        # handle mouse scrolling, only if the viewport size is bigger than the
        # Scroller size, and if the user allowed to do it
        
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
                    _touch.push()
                    _touch.apply_transform_2d(self.to_widget)
                    _touch.apply_transform_2d(self.to_parent)
                    super(Scroller, self).on_touch_down(touch)
                    _touch.pop()
                    touch.ungrab(self)

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
        if not self._viewport:
            return 0, 0
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
        if not self._viewport:
            return
        vp = self._viewport

        # update from size_hint
        if vp.size_hint_x is not None:
            vp.width = vp.size_hint_x * self.width
        if vp.size_hint_y is not None:
            vp.height = vp.size_hint_y * self.height

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
        Animation.stop_all(self, 'bar_alpha')
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
        widget.bind(size=self._trigger_update_from_scroll)
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
