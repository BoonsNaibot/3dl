'''
Created on Jul 27, 2013

@author: Divine
'''
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from listitems import ActionListItem, ListScreenItem
from kivy.uix.screenmanager import RiseInTransition
from kivy.lang import Builder
from uiux import Screen_

class ListScreen(Screen_):
    action_view = ObjectProperty(None)
    accordion_view = ObjectProperty(None)
    action_items = ListProperty([])
    list_items = ListProperty([])
    page = StringProperty('')
    page_number = NumericProperty(None)
    selection = ListProperty([])
    action_view_item = ObjectProperty(ActionListItem)
    accordion_view_item = ObjectProperty(ListScreenItem)
    
    def __init__(self, **kwargs):
        self.register_event_type('on_what')
        self.register_event_type('on_drop')
        self.register_event_type('on_archive')
        self.register_event_type('on_comments')
        self.register_event_type('on_new_item')
        self.register_event_type('on_due_date')
        self.register_event_type('on_importance')
        super(ListScreen, self).__init__(**kwargs)

    def on_pre_enter(self):
        if self.page:
            cursor = self.root_directory.cursor()
            action_items = [] #(i, u"", u"", 0, u"") for i in xrange(3)]
            list_items = []

            for i in cursor.execute("""
                                    SELECT ix, what, when_, why, how
                                    FROM [notebook]
                                    WHERE page=? AND ix>0
                                    ORDER BY ix
                                    """,
                                    (self.page,)):
                ix = i[0]#; print ix, i

                if ix < 4:
                    #action_items[ix] = i
                    action_items.append(i)
                else:
                    list_items.append(i)

            self.list_items, self.action_items = list_items, action_items

    def _args_converter(self, row_index, an_obj):
        _dict = {'drop_zones': [self.action_view,],
                 'screen': self}
        _dict['ix'], _dict['text'], _dict['when'], _dict['why'], _dict['how'] = an_obj
        _dict['why'] = bool(_dict['why'])

        if _dict['ix'] < 4:
            _dict['title_height_hint'] = (153./1136.)
            _dict['content_height_hint'] = (322./1136.)
            _dict['listview'] = self.action_view
            _dict['aleft'] = True

            if not _dict['text']:
                _dict['text'] = 'Drag a Task here.'
                _dict['disabled'] = True
        else:
            _dict['title_height_hint'] = 0.088
            _dict['content_height_hint'] = (190./1136.)
            _dict['drop_zones'].append(self.accordion_view)
            _dict['listview'] = self.accordion_view
            _dict['aleft'] = False

        return _dict

    def on_new_item(self, instance, text):
        text = text.lstrip()

        if text:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           INSERT INTO [notebook](ix, what, page)
                           VALUES((SELECT MAX(ROWID) FROM notebook)+1, ?, ?);
                           """,
                           (text, self.page))
            self.dispatch('on_pre_enter')#, self, self.page)

        instance.text = ''
        instance.focus = False

    def on_what(self, instance, value):
        instance.text = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE [notebook]
                       SET what=?
                       WHERE page=? AND ix=?;
                       """,
                       (value, self.page, instance.ix))

    def on_delete(self, instance):
        cursor = self.root_directory.cursor()
        ix = instance.parent.ix

        cursor.execute("""
                       DELETE FROM [notebook]
                       WHERE ix=? AND page=?;
                       """,
                       (ix, self.page))
        self.dispatch('on_pre_enter')

    def on_complete(self, instance):
        cursor = self.root_directory.cursor()
        ix = instance.parent.ix

        cursor.execute("""
                       INSERT INTO [archive]
                       SELECT * FROM notebook WHERE ix=? and page=?;
                       """,
                       (ix, self.page))
        self.dispatch('on_pre_enter')

    def on_importance(self, instance, value):
        instance.why = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE [notebook]
                       SET why=?
                       WHERE page=? AND ix=? AND what=?;
                       """,
                       (int(value), self.page, instance.ix, instance.text))

    def on_comments(self, instance, value):
        instance.how = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE [notebook]
                       SET how=?
                       WHERE page=? AND ix=? AND what=?;
                       """,
                       (value, self.page, instance.ix, instance.text))

    def on_due_date(self, instance, value):
        if value:
            dtms = self.manager.get_screen('Date-Time Mini-Screen')
            dtms.item = instance
            kwargs = {'duration': 0.2}
            self.dispatch('on_screen_change', 'Date-Time Mini-Screen', RiseInTransition, **kwargs)

    def on_drop(self, items):
        if items:
            cursor = self.root_directory.cursor()
            cursor.executemany("""
                               UPDATE [notebook]
                               SET what=?, when_=?, why=?, how=?
                               WHERE ix=? AND page=?;
                               """,
                               items)
            #self.dispatch('on_pre_enter')

    def on_archive(self, *args):
        screen = self.manager.get_screen('Archive Screen')
        screen.page, screen.page_number = self.page, self.page_number
        kwargs = {'direction': 'left', 'duration': 0.2}
        self.dispatch('on_screen_change', 'Archive Screen', kwargs)

Builder.load_string("""
#:import NavBar uiux.NavBar
#:import NewItemWidget uiux.NewItemWidget
#:import ActionListView listviews.ActionListView
#:import AccordionListView listviews.AccordionListView

<ListScreen>:
    name: 'List Screen'
    action_view: action_view_id
    accordion_view: accordion_view_id

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
            text: '5'
            state_color: app.no_color
            text_color: app.white
            font_size: self.width*0.5
            font_name: 'heydings_icons.ttf'
            size_hint: 0.18, 1
            pos_hint: {'center_x': 0.9, 'center_y': 0.5}
            on_press: root.dispatch('on_archive', 'Archive Screen', {'direction': 'left', 'duration': 0.2})

    ActionListView:
        id: action_view_id
        size_hint: 1, 0.4
        #pos_hint: {'x': 0, 'top': 0.8873}
        top: navbar_id.y - 1
        selection: root.selection
        list_item: root.action_view_item
        args_converter: root._args_converter
        data: root.action_items
    AccordionListView:
        id: accordion_view_id
        size_hint: 1, 0.4
        top: action_view_id.container.y
        list_item: root.accordion_view_item
        selection: root.selection
        args_converter: root._args_converter
        data: root.list_items    
    NewItemWidget:
        hint_text: 'Create New Task...'
        size_hint: 1, .086
        pos_hint: {'y': 0}
        on_text_validate: root.dispatch('on_new_item', *args[1:])
""")
