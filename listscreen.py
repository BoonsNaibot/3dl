'''
Created on Jul 27, 2013

@author: Divine
'''
from kivy.properties import ObjectProperty, ListProperty, StringProperty, NumericProperty
from datepickerminiscreen import DatePickerMiniScreen
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
                                    FROM notebook
                                    WHERE page=? AND ix>=0
                                    ORDER BY ix
                                    """,
                                    (self.page,)):
                ix = i[0]#; print ix, i

                if ix < 3:
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

        if _dict['ix'] < 3:
            _dict['title_height_hint'] = (153./1136.)
            _dict['content_height_hint'] = (322./1136.)
            _dict['listview'] = self.action_view
            _dict['aleft'] = True
            _dict['font_name'] = 'Oswald-Bold.otf'

            if not _dict['text']:
                _dict['text'] = 'Drag an Important Item here.'
                _dict['disabled'] = True
        else:
            _dict['title_height_hint'] = 0.088
            _dict['content_height_hint'] = (190./1136.)
            _dict['drop_zones'].append(self.accordion_view)
            _dict['listview'] = self.accordion_view
            _dict['aleft'] = False
            _dict['font_name'] = 'Walkway Bold.ttf'

        return _dict

    def on_new_item(self, instance, text):
        text = text.lstrip()

        if text:
            cursor = self.root_directory.cursor()
            cursor.execute("""
                           INSERT INTO notebook(ix, what, page)
                           VALUES((SELECT MAX(ROWID) FROM notebook), ?, ?);
                           """,
                           (text, self.page))
            self.dispatch('on_pre_enter')#, self, self.page)

        instance.text = ''
        instance.focus = False

    def on_what(self, instance, value):
        instance.text = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE notebook
                       SET what=?
                       WHERE page=? AND ix=?
                       """,
                       (value, self.page, instance.ix))

    def on_delete(self, instance):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       DELETE FROM notebook
                       WHERE ix=? AND what=? AND page=?
                       """,
                       (instance.parent.ix, instance.text, self.page))
        self.dispatch('on_pre_enter')

    def on_complete(self, instance):
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       INSERT INTO archive
                       VALUES((SELECT * FROM notebook WHERE ix=? and page=?));
                       """,
                       (instance.ix, self.page))
        self.dispatch('on_pre_enter')

    def on_importance(self, instance, value):
        instance.why = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE notebook
                       SET why=?
                       WHERE page=? AND ix=? AND what=?
                       """,
                       (int(value), self.page, instance.ix, instance.text))

    def on_comments(self, instance, value):
        instance.how = value
        cursor = self.root_directory.cursor()
        cursor.execute("""
                       UPDATE notebook
                       SET how=?
                       WHERE page=? AND ix=? AND what=?
                       """,
                       (value, self.page, instance.ix, instance.text))

    def on_due_date(self, instance, value):
        if value:
            manager = self.manager
            dpms = DatePickerMiniScreen(item=instance)
            manager.add_widget(dpms)
            manager.transition = RiseInTransition(duration=0.2)
            manager.current = 'DatePicker Mini-Screen'

    def on_drop(self, d):
        if d:
            items = ((v, k.text, self.page) for (k, v) in d.iteritems())
            cursor = self.root_directory.cursor()
            cursor.executemany("""
                               UPDATE notebook
                               SET ix=?
                               WHERE what=? AND page=?;
                               """,
                               items)
            """for k, v in d.iteritems():
                k.ix = v"""

Builder.load_string("""
#:import NavBar uiux
#:import NewItemWidget uiux.NewItemWidget
#:import ActionListView listviews.ActionListView
#:import AccordionListView listviews.AccordionListView

<ListScreen>:
    name: 'List Screen'
    action_view: action_view_id
    accordion_view: accordion_view_id

    NavBar:
        id: navbar_id
        size_hint: 1, .0775
        pos_hint:{'top': 0.9648}

        BoxLayout:
            size_hint: .9, .9
            pos_hint: {'center_x': .5, 'center_y': .5}

            Button_:
                font_size: self.height*0.5
                size_hint: 0.2, 1
                text: '< Lists'
                on_press: root.dispatch('on_screen_change', 'right', 'Pages Screen')
            Label:
                text: root.page
                size_hint: 0.6, 1
                font_size: self.height*0.8
                font_name: 'Walkway Bold.ttf'
                color: app.white
            Button_:
                font_size: self.height*0.5
                size_hint: 0.2, 1
                text: 'Archive >'

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
