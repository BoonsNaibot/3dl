'''
Created on Jul 23, 2013

@author: Divine
'''
from uiux import Screen_
from kivy.lang import Builder
from listitems import ArchiveScreenItem
from kivy.uix.screenmanager import SlideTransition
from kivy.properties import ObjectProperty, ListProperty

class ArchiveScreen(Screen_):
    list_items = ListProperty([])
    list_view = ObjectProperty(None)
    _item = ObjectProperty(ArchiveScreenItem)

    def on_pre_enter(self):
        if self.page:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           SELECT *
                           FROM archive
                           WHERE page=?
                           ORDER BY ROWID;
                           """,
                           (self.page,)):
            self.list_items = cursor.fetchall()

    def _args_converter(self, row_index, an_obj):
        dict = {'title_height_hint': 0.088,
                'content_height_hint': (190./1136.),
                'aleft': False,
                'font_name': 'Walkway Bold.ttf',
                'size_hint_y': None,
                'screen': self}
        dict['ix'], dict['text'], dict['when'], dict['why'], dict['how'] = an_obj
        dict['why'] = bool(dict['why'])
        return dict

    def on_delete(self, instance):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       DELETE FROM archive
                       WHERE ix=? AND what=? AND page=?;
                       """,
                       (instance.ix, instance.title, self.page))
        self.dispatch('on_pre_enter')

Builder.load_string("""
#:import NavBar uiux
#:import Button_ uiux.Button_
#:import AccordionListView listviews.AccordionListView

<ArchiveScreen>:
    name: 'Archive Screen'
    list_view: list_view_id

    NavBar:
        id: navbar_id
        size_hint: 1, .0775
        pos_hint:{'top': 0.9648}

        Label:
            text: root.page
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
            font_size: self.height*0.8
            font_name: 'Walkway Bold.ttf'
            color: app.white
        Button_:
            font_size: self.height*0.8
            size_hint: 0.09375, .682
            pos_hint: {'center_x': 0.08, 'center_y': 0.5}
            text: '< Back'
            on_press: root.dispatch('on_screen_change', 'right', 'List Screen')
            
    AccordionListView:
        id: list_view_id
        list_item: root._item
        args_converter: root._args_converter
        data: root.list_items
        size_hint: 1, 0.886
        top: navbar_id.y
""")


