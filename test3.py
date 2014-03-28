kv = '''
<ShaderTest>:
    canvas:
        Color:
            rgb: 0.1, 0.2, 0.3
        Rectangle:
            size: self.size
            pos: self.pos

    Button:
        text: 'foobar'
        size_hint: 0.5, 0.5
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}

'''
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.graphics import RenderContext
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.app import App
from kivy.graphics import Fbo, Color, Rectangle

class FboTest(Widget):
    def __init__(self, **kwargs):
        super(FboTest, self).__init__(**kwargs)

        # first step is to create the fbo and use the fbo texture on other
        # rectangle

        with self.canvas:
            # create the fbo
            self.fbo = Fbo(size=self.size)

            # show our fbo on the widget in different size
            Color(1, 1, 1)
            Rectangle(size=(32, 32), texture=self.fbo.texture)
            Rectangle(pos=(32, 0), size=(64, 64), texture=self.fbo.texture)
            Rectangle(pos=(96, 0), size=(128, 128), texture=self.fbo.texture)

        # in the second step, you can draw whatever you want on the fbo
        with self.fbo:
            Color(1, 0, 0, .8)
            Rectangle(size=(256, 64))
            Color(0, 1, 0, .8)
            Rectangle(size=(64, 256))

class ShaderTest(Widget):
    _vs = StringProperty('''
                         #ifdef GL_ES
                         precision highp float;
                         #endif
                         
                         varying vec2 vTexCoord;
                         
                         void main(void){
                            gl_Position = ftransform();;
                            
                            // Clean up inaccuracies
                            vec2 Pos;
                            Pos = sign(gl_Vertex.xy);
                            
                            gl_Position = vec4(Pos, 0.0, 1.0);
                            
                            // Image-space
                            vTexCoord = Pos * 0.5 + 0.5;
                            }''')
    hfs = StringProperty('''
                         #ifdef GL_ES
                         precision highp float;
                         #endif
                         
                         uniform sampler2D RTScene;
                         varying vec2 vTexCoord;
                         const float blurSize = 1.0/512.0;
                         
                         void main(void){
                            vec4 sum = vec4(0.0);
                            
                            // blur in y (vertical)
                            // take nine samples, with the distance blurSize between them
                            sum += texture2D(RTScene, vec2(vTexCoord.x - 4.0*blurSize, vTexCoord.y)) * 0.05;
                            sum += texture2D(RTScene, vec2(vTexCoord.x - 3.0*blurSize, vTexCoord.y)) * 0.09;
                            sum += texture2D(RTScene, vec2(vTexCoord.x - 2.0*blurSize, vTexCoord.y)) * 0.12;
                            sum += texture2D(RTScene, vec2(vTexCoord.x - blurSize, vTexCoord.y)) * 0.15;
                            sum += texture2D(RTScene, vec2(vTexCoord.x, vTexCoord.y)) * 0.16;
                            sum += texture2D(RTScene, vec2(vTexCoord.x + blurSize, vTexCoord.y)) * 0.15;
                            sum += texture2D(RTScene, vec2(vTexCoord.x + 2.0*blurSize, vTexCoord.y)) * 0.12;
                            sum += texture2D(RTScene, vec2(vTexCoord.x + 3.0*blurSize, vTexCoord.y)) * 0.09;
                            sum += texture2D(RTScene, vec2(vTexCoord.x + 4.0*blurSize, vTexCoord.y)) * 0.05;
                            
                            gl_FragColor = sum;
                            }''')
    vfs = StringProperty('''
                         #ifdef GL_ES
                         precision highp float;
                         #endif
                         
                         uniform sampler2D RTBlurH; // this should hold the texture rendered by the horizontal blur pass
                         varying vec2 vTexCoord;
                         const float blurSize = 1.0/512.0;
                         
                         void main(void){
                            vec4 sum = vec4(0.0);
                            
                            // blur in y (vertical)
                            // take nine samples, with the distance blurSize between them
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - 4.0*blurSize)) * 0.05;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - 3.0*blurSize)) * 0.09;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - 2.0*blurSize)) * 0.12;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y - blurSize)) * 0.15;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y)) * 0.16;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + blurSize)) * 0.15;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + 2.0*blurSize)) * 0.12;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + 3.0*blurSize)) * 0.09;
                            sum += texture2D(RTBlurH, vec2(vTexCoord.x, vTexCoord.y + 4.0*blurSize)) * 0.05;
                            
                            gl_FragColor = sum;
                            }''')

    def __init__(self, **kwargs):
        super(ShaderTest, self).__init__(**kwargs)
        self.canvas = RenderContext()
    #canvas = ObjectProperty(RenderContext(shader='blur.glsl'))

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

        with self.canvas:
            # create the fbo
            self.fbo = Fbo(size=self.size)

class ShaderTestApp(App):

    def build(self):
        return FboTest()

if __name__ == '__main__':
    #Builder.load_string(kv)
    ShaderTestApp().run()
