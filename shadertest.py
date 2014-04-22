from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import (StringProperty, ObjectProperty, ListProperty,
                             NumericProperty, DictProperty)
from kivy.graphics import (RenderContext, Fbo, Color, Rectangle,
                           Translate, PushMatrix, PopMatrix,
                           ClearColor, ClearBuffers)
from kivy.event import EventDispatcher
from kivy.base import EventLoop
from kivy.resources import resource_find

shader_header = '''
#ifdef GL_ES
precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;
'''

shader_uniforms = '''
uniform vec2 resolution;
uniform float time;
'''

effect_blur_h = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{{
    float dt = ({} / 4.0) * 1.0 / resolution.x;
    vec4 sum = vec4(0.0);
    sum += texture2D(texture, vec2(tex_coords.x - 4.0*dt, tex_coords.y))
                     * 0.05;
    sum += texture2D(texture, vec2(tex_coords.x - 3.0*dt, tex_coords.y))
                     * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x - 2.0*dt, tex_coords.y))
                     * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x - dt, tex_coords.y))
                     * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y))
                     * 0.16;
    sum += texture2D(texture, vec2(tex_coords.x + dt, tex_coords.y))
                     * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x + 2.0*dt, tex_coords.y))
                     * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x + 3.0*dt, tex_coords.y))
                     * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x + 4.0*dt, tex_coords.y))
                     * 0.05;
    return sum;
}}
'''

effect_blur_v = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{{
    float dt = ({} / 4.0)
                     * 1.0 / resolution.x;
    vec4 sum = vec4(0.0);
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - 4.0*dt))
                     * 0.05;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - 3.0*dt))
                     * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - 2.0*dt))
                     * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - dt))
                     * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y))
                     * 0.16;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + dt))
                     * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + 2.0*dt))
                     * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + 3.0*dt))
                     * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + 4.0*dt))
                     * 0.05;
    return sum;
}}
'''

class EffectBase(EventDispatcher):
    '''The base class for GLSL effects. It simply returns its input.

    See module documentation for more details.

    '''

    glsl = StringProperty(effect_trivial)
    '''The glsl string defining your effect function, see module
    documentation for more details.

    :attr:`glsl` is a :class:`~kivy.properties.StringProperty` and
    defaults to
    a trivial effect that returns its input.
    '''

    source = StringProperty('')
    '''The (optional) filename from which to load the :attr:`glsl`
    string.

    :attr:`source` is a :class:`~kivy.properties.StringProperty and
    defaults to ''.
    '''

    fbo = ObjectProperty(None, allownone=True)
    '''The fbo currently using this effect. The :class:`EffectBase
    automatically handles this.

    :attr:`fbo` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    def __init__(self, *args, **kwargs):
        super(EffectBase, self).__init__(*args, **kwargs)
        self.bind(fbo=self.set_fbo_shader)
        self.bind(glsl=self.set_fbo_shader)
        self.bind(source=self._load_from_source)

    def set_fbo_shader(self, *args):
        '''Sets the :class:`~kivy.graphics.Fbo`'s shader by splicing
        the :attr:`glsl` string into a full fragment shader.

        The full shader is made up of :code:`shader_header +
        shader_uniforms + self.glsl + shader_footer_effect`.
        '''
        if self.fbo is None:
            return
        self.fbo.set_fs(shader_header + shader_uniforms + self.glsl +
                        shader_footer_effect)

    def _load_from_source(self, *args):
        '''(internal) Loads the glsl string from a source file.'''
        source = self.source
        if not source:
            return
        filename = resource_find(source)
        if filename is None:
            return Logger.error('Error reading file {filename}'.
                                format(filename=source))
        with open(filename) as fileh:
            self.glsl = fileh.read()
        
class HorizontalBlurEffect(EffectBase):
    '''Blurs the input horizontally, with the width given by
    :attr:`~HorizontalBlurEffect.size`.'''

    size = NumericProperty(4.0)
    '''The blur width in pixels.

    size is a :class:`~kivy.properties.NumericProperty` and defaults to
    4.0.
    '''

    def __init__(self, *args, **kwargs):
        super(HorizontalBlurEffect, self).__init__(*args, **kwargs)
        self.do_glsl()

    def on_size(self, *args):
        self.do_glsl()

    def do_glsl(self):
        self.glsl = effect_blur_h.format(float(self.size))


class VerticalBlurEffect(EffectBase):
    '''Blurs the input vertically, with the width given by
    :attr:`~VerticalBlurEffect.size`.'''

    size = NumericProperty(4.0)
    '''The blur width in pixels.

    size is a :class:`~kivy.properties.NumericProperty` and defaults to
    4.0.
    '''

    def __init__(self, *args, **kwargs):
        super(VerticalBlurEffect, self).__init__(*args, **kwargs)
        self.do_glsl()

    def on_size(self, *args):
        self.do_glsl()

    def do_glsl(self):
        self.glsl = effect_blur_h.format(float(self.size))
        
class EffectFbo(Fbo):
    '''An :class:`~kivy.graphics.Fbo` with extra facility to
    attempt setting a new shader, see :meth:`set_fs`.
    '''
    def __init__(self, *args, **kwargs):
        super(EffectFbo, self).__init__(*args, **kwargs)
        self.texture_rectangle = None

    def set_fs(self, value):
        '''Attempt to set the fragment shader to the given value.
        If setting the shader fails, resets the old one and raises an
        exception.
        '''
        shader = self.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('Setting new shader failed.')


class EffectWidget(Widget):
    '''
    Widget with the ability to apply a series of graphical effects to
    its children. See module documentation for full information on
    setting effects and creating your own.
    '''

    texture = ObjectProperty(None)
    '''The output texture of our final :class:`~kivy.graphics.Fbo` after
    all effects have been applied.

    texture is an :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    effects = ListProperty([])
    '''List of all the effects to be applied.

    effects is a :class:`ListProperty` and defaults to [].
    '''

    fbo_list = ListProperty([])
    '''(internal) list of all the fbos that are being used to apply
    the effects.

    fbo_list is a :class:`ListProperty` and defaults to [].
    '''

    _bound_effects = ListProperty([])
    '''(internal) list of effect classes that have been given an fbo to
    manage. This is necessary so that the fbo can be removed it the
    effect is no longer in use.

    _bound_effects is a :class:`ListProperty` and defaults to [].
    '''

    def __init__(self, **kwargs):
        # Make sure opengl context exists
        EventLoop.ensure_window()

        self.canvas = RenderContext(use_parent_projection=True,
                                    use_parent_modelview=True)

        with self.canvas:
            self.fbo = Fbo(size=self.size)
        with self.fbo.before:
            PushMatrix()
            self.fbo_translation = Translate(-self.x, -self.y, 0)
        with self.fbo:
            Color(0, 0, 0)
            self.fbo_rectangle = Rectangle(size=self.size)
        with self.fbo.after:
            PopMatrix()

        super(EffectWidget, self).__init__(**kwargs)

        Clock.schedule_interval(self._update_glsl, 0)

        self.bind(pos=self._update_translation,
                  size=self.refresh_fbo_setup,
                  effects=self.refresh_fbo_setup)

        self.refresh_fbo_setup()

    def _update_translation(self, *args):
        '''(internal) Makes sure everything is translated correctly to
        appear in the fbo.'''
        self.fbo_translation.x = -self.x
        self.fbo_translation.y = -self.y

    def _update_glsl(self, *largs):
        '''(internal) Passes new time and resolution uniform
        variables to the shader.
        '''
        time = Clock.get_boottime()
        resolution = [float(size) for size in self.size]
        self.canvas['time'] = time
        self.canvas['resolution'] = resolution

        for fbo in self.fbo_list:
            fbo['time'] = time
            fbo['resolution'] = resolution

    def refresh_fbo_setup(self, *args):
        '''(internal) Creates and assigns one :class:`~kivy.graphics.Fbo`
        per effect, and makes sure all sizes etc. are correct and
        consistent.
        '''
        # Add/remove fbos until there is one per effect
        while len(self.fbo_list) < len(self.effects):
            
            with self.canvas:
                new_fbo = EffectFbo(size=self.size)
            with new_fbo:
                Color(1, 1, 1, 1)
                new_fbo.texture_rectangle = Rectangle(size=self.size)
                new_fbo.texture_rectangle.size = self.size
            self.fbo_list.append(new_fbo)

        while len(self.fbo_list) > len(self.effects):
            old_fbo = self.fbo_list.pop()
            self.canvas.remove(old_fbo)

        # Remove fbos from unused effects
        for effect in self._bound_effects:
            if effect not in self.effects:
                effect.fbo = None
        self._bound_effects = self.effects

        # Do resizing etc.
        self.fbo.size = self.size
        self.fbo_rectangle.size = self.size

        for i in range(len(self.fbo_list)):
            self.fbo_list[i].size = self.size
            self.fbo_list[i].texture_rectangle.size = self.size

        # If there are no effects, just draw our main fbo
        if len(self.fbo_list) == 0:
            self.texture = self.fbo.texture
            return

        for i in range(1, len(self.fbo_list)):
            fbo = self.fbo_list[i]
            fbo.texture_rectangle.texture = self.fbo_list[i - 1].texture

        # Build effect shaders
        for effect, fbo in zip(self.effects, self.fbo_list):
            effect.fbo = fbo

        self.fbo_list[0].texture_rectangle.texture = self.fbo.texture
        self.texture = self.fbo_list[-1].texture

    def add_widget(self, widget):
        # Add the widget to our Fbo instead of the normal canvas
        c = self.canvas
        self.canvas = self.fbo
        super(EffectWidget, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        # Remove the widget from our Fbo instead of the normal canvas
        c = self.canvas
        self.canvas = self.fbo
        super(EffectWidget, self).remove_widget(widget)
        self.canvas = c

    def clear_widgets(self, children=None):
        # Clear widgets from our Fbo instead of the normal canvas
        c = self.canvas
        self.canvas = self.fbo
        super(EffectWidget, self).clear_widgets(children)
        self.canvas = c

Builder.load_string('''
<EffectWidget>:
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            texture: self.texture
            pos: self.pos
            size: self.size
''')
