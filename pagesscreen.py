'''
Created on Jul 23, 2013

@author: Divine
'''
from uiux import Screen_
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.animation import Animation
from listitems import PagesScreenItem
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import ObjectProperty, ListProperty

class ConfigPanel(Widget):
    state = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super(ConfigPanel, self).on_touch_down(touch)
        else:
            widget = self.parent
            widget._anim = Animation(x=0, y=0, duration=0.2)
            widget._anim.bind(on_complete=lambda *_: widget.remove_widget(self))
            widget._anim.start(widget)
            widget.polestar = None
            return True

class PagesScreen(Screen_):
    pages = ListProperty([])
    list_view = ObjectProperty(None)
    list_item = ObjectProperty(PagesScreenItem)

    def __init__(self, **kwargs):
        self.register_event_type('on_what')
        self.register_event_type('on_new_item')
        self.register_event_type('on_settings')
        self.register_event_type('on_selected_page')
        self.register_event_type('on_root_directory')
        super(PagesScreen, self).__init__(**kwargs)

    def on_enter(self):
        if self.root_directory:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           UPDATE [table of contents]
                           SET bookmark=0
                           """)

    def _args_converter(self, row_index, an_obj):
        dict = {'page_number': an_obj[0],
                'text': an_obj[1],
                'size_hint_y': None,
                'screen': self}
        return dict

    def on_root_directory(self, *args):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       SELECT page_number, page
                       FROM [table of contents]
                       ORDER BY page_number;
                       """)
        self.pages = cursor.fetchall()

    def on_selected_page(self, text, index):
        manager = self.manager
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       SELECT COUNT(what)
                       FROM notebook
                       WHERE page=? AND ix<4 AND what<>'';
                       """,
                       (text,))
        i = cursor.fetchall()[0][0]

        if i < 3:
            screen_name = 'List Screen'
        else:
            screen_name = 'QuickView Screen'

        screen = manager.get_screen(screen_name)
        screen.page = text
        screen.page_number = index
        kwargs = {'direction': 'left', 'duration': 0.2}
        self.dispatch('on_screen_change', screen_name, kwargs)

    def on_status_bar(self, *args):
        self.list_view.scroll_to()

    def on_settings(self, *args):
        if not self.polestar:
            self.polestar = ConfigPanel()
            self.add_widget(self.polestar)
            self._anim = Animation(x=self.size[0]*0.75, duration=0.2)
            self._anim.start(self)

    def on_new_item(self, instance, text):
        text = text.lstrip()

        if text:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           INSERT INTO [table of contents](page_number, page)
                           VALUES((SELECT IFNULL(MAX(ROWID), 0) FROM [table of contents])+1, ?);
                           """,
                           (text,))
            #cursor.execute('commit')
            self.dispatch('on_root_directory')

        instance.text = ''
        instance.focus = False

    def on_what(self, instance, value):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE [table of contents]
                       SET page=?
                       WHERE page_number=?;
                       """,
                       (instance.text, instance.page_number))

    def on_delete(self, instance):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       DELETE FROM [table of contents]
                       WHERE page_number=? AND page=?;
                       """,
                       (instance.page_number, instance.text))
        self.dispatch('on_root_directory')
        self.polestar = None

    def on_leave(self, *args):
        cursor = self.root_directory.cursor()
        screen = self.manager.current_screen
        cursor.execute("""
                       UPDATE [table of contents]
                       SET bookmark=1
                       WHERE page_number=? AND page=?;
                       """,
                       (screen.page_number, screen.page))

Builder.load_string("""
#:import NavBar uiux.NavBar
#:import Button_ uiux.Button_
#:import NewItemWidget uiux.NewItemWidget
#:import DNDListView listviews.DNDListView

<ConfigPanel>:
    size_hint: 0.75, 1
    pos_hint: {'right':0, 'y':0}
    canvas.before:
        Color:
            rgb: app.smoke_white
        Rectangle:
            pos: self.pos
            size: self.size

<PagesScreen>:
    name: 'Pages Screen'
    list_view: list_view_id

    NavBar:
        id: navbar_id
        text: 'Lists'
        font_size: self.height*0.8

        Button_:
            font_size: self.height*0.8
            font_name: 'breezi_font-webfont.ttf'
            size_hint: 0.09375, .682
            pos_hint: {'center_x': 0.08, 'center_y': 0.5}
            text: 'E'
            on_press: root.dispatch('on_settings')
            
    DNDListView:
        id: list_view_id
        data: root.pages
        selection_mode: 'None'
        list_item: root.list_item
        args_converter: root._args_converter
        size_hint: 1, .8
        pos_hint: {'top': 0.8873}
    NewItemWidget:
        hint_text: 'Create New List...'
        size_hint: 1, .086
        pos_hint: {'y': 0}
        on_text_validate: root.dispatch('on_new_item', *args[1:])
""")


