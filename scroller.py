__all__ = ('Scroller', )

from functools import partial
from kivy.animation import Animation
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.stencilview import StencilView
from kivy.metrics import sp
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import NumericProperty, BooleanProperty, AliasProperty, \
    ObjectProperty, ListProperty, OptionProperty
from kivy.lang import Builder


# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = sp(Config.getint('widgets', 'scroll_distance'))


class Scroller(StencilView):
    '''Scroller class. See module documentation for more information.

    .. versionchanged:: 1.7.0

        `auto_scroll`, `scroll_friction`, `scroll_moves`, `scroll_stoptime' has
        been deprecated, use :data:`effect_cls` instead.
    '''

    scroll_distance = NumericProperty(_scroll_distance)
    '''Distance to move before scrolling the :class:`Scroller`, in pixels. As
    soon as the distance has been traveled, the :class:`Scroller` will start
    to scroll, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :data:`scroll_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 20 (pixels), according to the default value in user
    configuration.
    '''

    scroll_timeout = NumericProperty(_scroll_timeout)
    '''Timeout allowed to trigger the :data:`scroll_distance`, in milliseconds.
    If the user has not moved :data:`scroll_distance` within the timeout,
    the scrolling will be disabled, and the touch event will go to the children.

    :data:`scroll_timeout` is a :class:`~kivy.properties.NumericProperty`,
    default to 55 (milliseconds), according to the default value in user
    configuration.

    .. versionchanged:: 1.5.0
        Default value changed from 250 to 55.
    '''

    scroll_x = NumericProperty(0.)
    '''X scrolling value, between 0 and 1. If 0, the content's left side will
    touch the left side of the Scroller. If 1, the content's right side will
    touch the right side.

    This property is controled by :class:`Scroller` only if
    :data:`do_scroll_x` is True.

    :data:`scroll_x` is a :class:`~kivy.properties.NumericProperty`,
    default to 0.
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

    do_scroll_x = BooleanProperty(True)
    '''Allow scroll on X axis.

    :data:`do_scroll_x` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    do_scroll_y = BooleanProperty(True)
    '''Allow scroll on Y axis.

    :data:`do_scroll_y` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    def _get_do_scroll(self):
        return (self.do_scroll_x, self.do_scroll_y)

    def _set_do_scroll(self, value):
        if type(value) in (list, tuple):
            self.do_scroll_x, self.do_scroll_y = value
        else:
            self.do_scroll_x = self.do_scroll_y = bool(value)
    do_scroll = AliasProperty(_get_do_scroll, _set_do_scroll,
                                bind=('do_scroll_x', 'do_scroll_y'))
    '''Allow scroll on X or Y axis.

    :data:`do_scroll` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`do_scroll_x` + :data:`do_scroll_y`)
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

    def _get_hbar(self):
        # must return (x, width) in %
        # calculate the viewport size / Scroller size %
        if self._viewport is None:
            return 0, 1.
        vw = self._viewport.width
        w = self.width
        if vw < w or vw == 0:
            return 0, 1.
        pw = max(0.01, w / float(vw))
        sx = min(1.0, max(0.0, self.scroll_x))
        px = (1. - pw) * sx
        return (px, pw)

    hbar = AliasProperty(_get_hbar, None, bind=(
        'scroll_x', '_viewport', 'viewport_size'))
    '''Return a tuple of (position, size) of the horizontal scrolling bar.

    .. versionadded:: 1.2.0

    The position and size are normalized between 0-1, and represent a
    percentage of the current Scroller height. This property is used
    internally for drawing the little horizontal bar when you're scrolling.

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

    effect_cls = ObjectProperty(DampedScrollEffect, allownone=True)
    '''Class effect to instanciate for X and Y axis.

    .. versionadded:: 1.7.0

    :data:`effect_cls` is a :class:`~kivy.properties.ObjectProperty`, default to
    :class:`DampedScrollEffect`.
    '''

    effect_x = ObjectProperty(None, allownone=True)
    '''Effect to apply for the X axis. If None is set, an instance of
    :data:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :data:`effect_x` is a :class:`~kivy.properties.ObjectProperty`, default to
    None
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

    def _set_viewport_size(self, instance, value):
        self.viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self.viewport_size = value.size

    def __init__(self, **kwargs):
        self._touch = None
        self._trigger_update_from_scroll = Clock.create_trigger(
            self.update_from_scroll, -1)
        super(Scroller, self).__init__(**kwargs)
        if self.effect_x is None and self.effect_cls is not None:
            self.effect_x = self.effect_cls(target_widget=self._viewport)
        if self.effect_y is None and self.effect_cls is not None:
            self.effect_y = self.effect_cls(target_widget=self._viewport)
        self.bind(
            width=self._update_effect_x_bounds,
            height=self._update_effect_y_bounds,
            viewport_size=self._update_effect_bounds,
            _viewport=self._update_effect_widget,
            scroll_x=self._trigger_update_from_scroll,
            scroll_y=self._trigger_update_from_scroll,
            pos=self._trigger_update_from_scroll,
            size=self._trigger_update_from_scroll)

        self._update_effect_widget()
        self._update_effect_x_bounds()
        self._update_effect_y_bounds()

    def on_effect_x(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_x)
            value.target_widget = self._viewport

    def on_effect_y(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_y)
            value.target_widget = self._viewport

    def on_effect_cls(self, instance, cls):
        self.effect_x = self.effect_cls(target_widget=self._viewport)
        self.effect_x.bind(scroll=self._update_effect_x)
        self.effect_y = self.effect_cls(target_widget=self._viewport)
        self.effect_y.bind(scroll=self._update_effect_y)

    def _update_effect_widget(self, *args):
        if self.effect_x:
            self.effect_x.target_widget = self._viewport
        if self.effect_y:
            self.effect_y.target_widget = self._viewport

    def _update_effect_x_bounds(self, *args):
        if not self._viewport or not self.effect_x:
            return
        self.effect_x.min = -(self.viewport_size[0] - self.width)
        self.effect_x.max = 0
        self.effect_x.value = self.effect_x.min * self.scroll_x

    def _update_effect_y_bounds(self, *args):
        if not self._viewport or not self.effect_y:
            return
        self.effect_y.min = -(self.viewport_size[1] - self.height)
        self.effect_y.max = 0
        self.effect_y.value = self.effect_y.min * self.scroll_y

    def _update_effect_bounds(self, *args):
        if not self._viewport:
            return
        if self.effect_x:
            self._update_effect_x_bounds()
        if self.effect_y:
            self._update_effect_y_bounds()

    def _update_effect_x(self, *args):
        vp = self._viewport
        if not vp or not self.effect_x:
            return
        sw = vp.width - self.width
        if sw < 1:
            return
        sx = self.effect_x.scroll / float(sw)
        self.scroll_x = -sx
        self._trigger_update_from_scroll()

    def _update_effect_y(self, *args):
        vp = self._viewport
        if not vp or not self.effect_y:
            return
        sh = vp.height - self.height
        if sh < 1:
            return
        sy = self.effect_y.scroll / float(sh)
        self.scroll_y = -sy
        self._trigger_update_from_scroll()

    def _change_touch_mode(self, *largs):
        if not self._touch:
            return
        uid = self._get_uid()
        touch = self._touch
        ud = touch.ud[uid]
        if ud['mode'] != 'unknown' or ud['user_stopped']:
            return
        if self.do_scroll_y and self.effect_y:
            self.effect_y.cancel()
        # XXX the next line was in the condition. But this stop
        # the possibily to "drag" an object out of the Scroller in the
        # non-used direction: if you have an horizontal Scroller, a
        # vertical gesture will not "stop" the scroll view to look for an
        # horizontal gesture, until the timeout is done.
        # and touch.dx + touch.dy == 0:
        touch.ungrab(self)
        self._touch = None
        # correctly calculate the position of the touch inside the
        # Scroller
        touch.push()
        touch.apply_transform_2d(self.to_widget)
        touch.apply_transform_2d(self.to_parent)
        super(Scroller, self).on_touch_down(touch)
        touch.pop()
        return

    def on_touch_down(self, touch):
        # handle mouse scrolling, only if the viewport size is bigger than the
        # Scroller size, and if the user allowed to do it
        
        if self.collide_point(*touch.pos):
                
            if touch.is_mouse_scrolling:
                vp = self._viewport
    
                if vp and 'button' in touch.profile and \
                    touch.button.startswith('scroll'):
                    btn = touch.button
                    m = self.scroll_distance
                    e = None
        
                    if (self.effect_x and self.do_scroll_y and vp.height > self.height
                            and btn in ('scrolldown', 'scrollup')):
                        e = self.effect_y
        
                    elif (self.effect_y and self.do_scroll_x and vp.width > self.width
                            and btn in ('scrollleft', 'scrollright')):
                        e = self.effect_x
        
                    if e:
                        if btn in ('scrolldown', 'scrollleft'):
                            e.value = max(e.value - m, e.min)
                            e.velocity = 0
                        elif btn in ('scrollup', 'scrollright'):
                            e.value = min(e.value + m, e.max)
                            e.velocity = 0
                        touch.ud[self._get_uid('svavoid')] = True
                        e.trigger_velocity_update()
                        return True
            
            
            elif self.mode == 'scrolling':
                self.effect_y.cancel()
            # no mouse scrolling, so the user is going to drag the Scroller with
            # this touch.
            touch.grab(self)
            touch.ud[uid] = {
                'touch_down': touch,
                'mode': 'unknown',
                'dy': 0,
                'time': touch.time_start}
            if self.do_scroll_y and self.effect_y:
                self.effect_y.start(touch.y)
            Clock.schedule_once(self._change_touch_mode,
                                self.scroll_timeout / 1000.)
            return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            if (abs(touch.dy) < self.scroll_distance):
                touch.ungrab(self)

                if 'touch_down' in touch.ud:
                    _touch = touch.ud.pop('touch_down')
                    _touch.push()
                    _touch.apply_transform_2d(self.to_widget)
                    _touch.apply_transform_2d(self.to_parent)
                    ret = super(Scroller, self).on_touch_down(touch)
                    _touch.pop()
                    return ret

            elif self.mode <> 'scrolling':
                touch.ud['dy'] += abs(touch.dy)
                self.mode = 'scrolling'
            
            return False
            
        else:
            # check if the minimum distance has been travelled
    
            if mode == 'scroll':
                self.effect_y.update(touch.y)
                ud['dt'] = touch.time_update - ud['time']
                ud['time'] = touch.time_update
                #ud['user_stopped'] = True
            return True

    def on_touch_up(self, touch):
        if 'touch_down' in touch.ud:
            del touch.ud['touch_down']

        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            uid = self._get_uid()
            ud = touch.ud[uid]
            if self.do_scroll_y and self.effect_y:
                self.effect_y.stop(touch.y)
            if ud['mode'] == 'unknown':
                # we must do the click at least..
                # only send the click if it was not a click to stop
                # autoscrolling
                if not ud['user_stopped']:
                    super(Scroller, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
        else:
            if self._touch is not touch and self.uid not in touch.ud:
                super(Scroller, self).on_touch_up(touch)

        # if we do mouse scrolling, always accept it
        if touch.is_mouse_scrolling:
            return True

        return self._get_uid() in touch.ud

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

    def _do_touch_up(self, touch, *largs):
        super(Scroller, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(Scroller, self).on_touch_up(touch)
        touch.grab_current = None

Builder.load_string("""
<Scroller>:
    canvas.after:
        Color:
            rgba: self.bar_color[:3] + [self.bar_color[3] * self.bar_alpha if self.do_scroll_y else 0]
        Rectangle:
            pos: self.right - self.bar_width - self.bar_margin, self.y + self.height * self.vbar[0]
            size: self.bar_width, self.height * self.vbar[1]
        Color:
            rgba: self.bar_color[:3] + [self.bar_color[3] * self.bar_alpha if self.do_scroll_x else 0]
        Rectangle:
            pos: self.x + self.width * self.hbar[0], self.y + self.bar_margin
            size: self.width * self.hbar[1], self.bar_width
""")
