'''
Created on Jul 27, 2013

@author: Divine
'''

from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from listitems import QuickViewScreenItem
from kivy.utils import escape_markup
from kivy.lang import Builder
from uiux import Screen_

class QuickViewScreen(Screen_):
    _item = ObjectProperty(QuickViewScreenItem)
    action_items = ListProperty([])
    page = StringProperty('')
    page_number = NumericProperty(None)
    watchwords = ListProperty(['Go', 'Pickup', 'Start', 'Begin', 'Finish', 'Pay'])
    
    def __init__(self, **kwargs):
    	self.register_event_type('on_full_list')
    	super(QuickViewScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        if self.page:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           SELECT ix, what, when_, why, how
                           FROM [notebook]
                           WHERE page=? AND ix<4
                           ORDER BY ix
                           """,
                           (self.page,))
            self.action_items = cursor.fetchall()

    def on_full_list(self, *args):
        screen = self.manager.get_screen('List Screen')
        screen.page, screen.page_number = self.page, self.page_number
        kwargs = {'direction': 'left', 'duration': 0.2}
        self.dispatch('on_screen_change', 'List Screen', kwargs)

    def _args_converter(self, row_index, an_obj):
        _dict = {'size_hint_y': 0.3,
                 'screen': self}
        _dict['ix'], _dict['text'], _dict['when'], _dict['why'], _dict['how'] = an_obj
        what = self.format_title(_dict['text'])
        
        if what:
            _dict['text'] = what
            _dict['markup'] = True

        return _dict

    def format_title(self, str):
    	watchwords = self.watchwords

    	for word in watchwords:
            if str.startswith(word + ' '):
                return '[b]' + word + '[/b]' + escape_markup(str[(len(word)-1):])

    def on_delete(self, instance):
        cursor = self.root_directory.cursor()
        ix = instance.parent.ix

        cursor.execute("""
                       DELETE FROM [notebook]
                       WHERE ix=? AND page=? AND page_number=?;
                       """,
                       (ix, self.page, self.page_number))
        self.polestar = None
        self.dispatch('on_pre_enter')

    def on_complete(self, instance):
        cursor = self.root_directory.cursor()
        ix = instance.parent.ix

        cursor.execute("""
                       INSERT INTO [archive]
                       SELECT * FROM [notebook] WHERE ix=? AND page=? AND page_number=?;
                       """,
                       (ix, self.page, self.page_number))
        self.polestar = None
        self.dispatch('on_pre_enter')

Builder.load_string("""
#:import NavBar uiux.NavBar
#:import QuickListView listviews
#:import QuickViewScreenItem listitems.QuickViewScreenItem

<QuickViewScreen>:
    name: 'QuickView Screen'
        
    NavBar:
        id: navbar_id
        text: root.page
        size_hint: 1, 0.1127
        font_size: root.width*0.3
        pos_hint:{'top': 1, 'x': 0}

        Button_:
            text: '<D'
            state_color: app.no_color
            text_color: app.white
            font_size: self.width*0.5
            font_name: 'breezi_font-webfont.ttf'
            size_hint: 0.18, 1
            pos_hint: {'center_x': 0.08, 'center_y': 0.5}
            on_press: root.dispatch('on_screen_change', 'Pages Screen', {'direction': 'right', 'duration': 0.2})
        Button_:
            text: 'd>'
            state_color: app.no_color
            text_color: app.white
            font_size: self.width*0.5
            font_name: 'breezi_font-webfont.ttf'
            size_hint: 0.18, 1
            pos_hint: {'center_x': 0.9, 'center_y': 0.5}
            on_press: root.dispatch('on_full_list')

    QuickListView:
        data: root.action_items
        args_converter: root._args_converter
        list_item: root._item
        size_hint: 1, 0.8873
        top: navbar_id.y
""")        
