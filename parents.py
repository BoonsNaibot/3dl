"""
Experiment with circular references
"""

from kivy.uix.widget import Widget
from kivy.uix.layout import Layout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout

class Widget(Widget):

    def add_widget(self, *args):
        super(Widget, self).add_widget(*args)
        args[0].parent = self.proxy_ref

class Layout(Layout):

    def add_widget(self, *args):
        super(Layout, self).add_widget(*args)
        args[0].parent = self.proxy_ref

class BoxLayout(BoxLayout):

    def add_widget(self, *args):
        super(BoxLayout, self).add_widget(*args)
        args[0].parent = self.proxy_ref

class GridLayout(GridLayout):

    def add_widget(self, *args):
        super(GridLayout, self).add_widget(*args)
        args[0].parent = self.proxy_ref

class FloatLayout(FloatLayout):

    def add_widget(self, *args):
        super(FloatLayout, self).add_widget(*args)
        args[0].parent = self.proxy_ref
