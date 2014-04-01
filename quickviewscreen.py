'''
Created on Jul 27, 2013

@author: Divine
'''

from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.utils import escape_markup
from kivy.lang import Builder
from uiux import Screen_

class QuickViewScreen(Screen_):
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
                           FROM notebook
                           WHERE page=? AND ix<3
                           ORDER BY ix
                           """,
                           (self.page,))
            self.action_items = cursor.fetchall()

    def on_full_list(self, *args):
        list_screen = self.manager.get_screen('List Screen')
        list_screen.page = self.page
        list_screen.page_number = self.page_number
        kwargs = {'direction': 'left', 'duration': 0.2}
        self.dispatch('on_screen_change', 'List Screen', **kwargs)

    def _args_converter(self, row_index, an_obj):
        dict = {'size_hint_y': .3,
                'screen': self}
        dict['ix'], dict['text'], dict['when'], dict['why'], dict['how'] = an_obj
        what = self.format_title(dict['text'])
        dict['how'] = ''
        
        if what:
	    dict['text'] = what
	    dict['markup'] = True

        return dict

    def format_title(self, str):
	watchwords = self.watchwords
	
	for word in watchwords:
	    if str.startswith(word + ' '):
		return '[b]' + word + '[/b]' + escape_markup(str[(len(word)-1):])

Builder.load_string("""
#:import NavBar uiux
#:import QuickListView listviews
#:import QuickViewScreenItem listitems.QuickViewScreenItem

<QuickViewScreen>:
    name: 'QuickView Screen'
        
    NavBar:
        id: navbar_id
        text: root.page
        font_size: self.height*.8

        Button_:
            font_size: 12
            size_hint: 0.1, 1
            text: '< Lists'
            on_press: root.dispatch('on_screen_change', 'Pages Screen', **{'direction': 'right', 'duration': 0.2})
        Button_:
            font_size: 12
            size_hint: .1, 1
            text: 'Full List >'
            on_press: root.dispatch('on_full_list')

    QuickListView:
        data: root.action_items
        args_converter: root._args_converter
        list_item: QuickViewScreenItem
        size_hint: 1, 0.8873
        top: navbar_id.y
""")        
