'''
Created on Jul 23, 2013

@author: Divine
'''
from weakref import proxy
from kivy.lang import Builder
from weakreflist import WeakList
from listitems import NoteItem, NoteContent
from uiux import Screen_, Clickable, Deletable
from kivy.properties import ListProperty, ObjectProperty, OptionProperty

class ArchiveScreenItemTitle(Deletable, Clickable):
    aleft = True
    screen = None
    listview = None
    height_hint = (2.0/15.0)
    state = OptionProperty('normal', options=('delete', 'down', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.state <> 'normal':
                self.state = 'normal'
                return True

        else:
            return super(ArchiveScreenItemTitle, self).on_touch_down(touch)

class ArchiveContent(NoteContent):
    screen = None
    height_hint = (322./1136.)
        
class ArchiveScreenItem(NoteItem):
    pass

class ArchiveScreen(Screen_):
    list_items = ListProperty([])
    list_view = ObjectProperty(None)
    selection = ListProperty(WeakList())
    _item = ObjectProperty(proxy(ArchiveScreenItem))
        
    def on_list_view(self, instance, value):
        if value:
            super(ArchiveScreen, self).on_list_view(instance, value)
            ArchiveScreenItemTitle.screen = instance.proxy_ref
            ArchiveScreenItemTitle.listview = value

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
        _dict = {}
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

<ArchiveContent>:
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos

    DoubleClickButton:
        size_hint: 0.75, 0.3
        pos_hint: {'x': 0.05, 'top': 1}
        icon_text: 'Due:'
        icon_font_name: 'Walkway Bold.ttf'
        font_size: root.width*0.043
        text: root.when
        text_color: root.text_color
        on_double_click_switch: root.screen.dispatch('on_due_date', root.parent, args[1])
    DoubleClickButton:
        size_hint: 0.1, 0.3
        pos_hint: {'x': 0.85, 'top': 1}
        icon_text: '!'
        text: ''
        font_size: root.width*0.07
        #font_size: self.height*0.421875
        text_color: app.blue if self.double_click_switch else app.dark_gray
        double_click_switch: root.why
        on_double_click_switch: root.dispatch('on_importance', *args)
    Label:
        id: icon_id
        text: 'Notes:'
        font_name: 'Walkway Bold.ttf'
        #font_size: self.height*0.421875
        font_size: root.width*0.05
        color: root.text_color
        size_hint: 0.17, 0.3
        disabled_color: self.color
        pos_hint: {'x': 0.05, 'top': 0.5}
        text_size: self.size
        valign: 'top'
    EditButton:
        text: root.how
        max_chars: 70
        size_hint: 0.72, 0.5
        top: icon_id.top
        x: icon_id.right
        font_name: 'Walkway Bold.ttf'
        font_size: root.width*0.05
        text_color: root.text_color

<ArchiveScreenItem>:
    title: title_id
    content: content_id
    size_hint: 1, None
    text_color: app.dark_blue
    state_color: app.no_color if title_id.state in ('down', 'dragged') else app.white

    ArchiveScreenItemTitle:
        id: title_id
        text: root.text
        size_hint: 1, None
        pos_hint: {'x': 0, 'top': 1}
        font_size: (self.height*0.3)
        text_color: root.text_color
        state_color: root.state_color
        on_release: root.listview.handle_selection(root)
    ArchiveContent:
        id: content_id
        disabled: True
        why: root.why
        how: root.how
        when: root.when
        top: title_id.y
        pos_hint: {'x': 0}
        size_hint: 1, None
        text_color: root.text_color
        state_color: root.state_color
        height: root.screen.height*self.height_hint

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


