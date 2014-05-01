'''
Created on Jul 23, 2013

@author: Divine
'''
from uiux import Screen_
from kivy.lang import Builder
from kivy.weakreflist import WeakList
from listitems import ArchiveScreenItem
from kivy.properties import ObjectProperty, ListProperty

class ArchiveScreen(Screen_):
    list_items = ListProperty([])
    list_view = ObjectProperty(None)
    selection = ListProperty(WeakList())
    _item = ObjectProperty(ArchiveScreenItem)

    def on_pre_enter(self):
        if self.page:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           SELECT ix, what, when_, why, how
                           FROM [archive]
                           WHERE page=?
                           ORDER BY ROWID;
                           """,
                           (self.page,))
            self.list_items = cursor.fetchall()

    def _args_converter(self, row_index, an_obj):
        _dict = {'title_height_hint': (153./1136.),
                 'content_height_hint': (322./1136.),
                 'aleft': True,
                 'screen': self.proxy_ref}
        _dict['ix'], _dict['text'], _dict['when'], _dict['why'], _dict['how'] = an_obj
        _dict['why'] = bool(_dict['why'])
        return _dict

    def on_delete(self, instance):
        ix = instance.parent.ix
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       DELETE FROM [archive]
                       WHERE ix=? AND what=? AND page=?;
                       """,
                       (ix, instance.text, self.page))
        self.polestar = lambda : None
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
        text: 'Archive'
        size_hint: 1, 0.1127
        font_size: root.width*0.3
        pos_hint:{'top': 1, 'x': 0}

        Button_:
            text: '<q'
            state_color: app.no_color
            text_color: app.white
            font_size: self.width*0.5
            font_name: 'breezi_font-webfont.ttf'
            size_hint: 0.18, 1
            pos_hint: {'center_x': 0.08, 'center_y': 0.5}
            on_press: root.dispatch('on_screen_change', 'List Screen', {'direction': 'right', 'duration': 0.2})
            
    AccordionListView:
        id: list_view_id
        list_item: root._item
        args_converter: root._args_converter
        data: root.list_items
        size_hint: 1, 0.886
        top: navbar_id.y
""")


