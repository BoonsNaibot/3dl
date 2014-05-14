'''
Created on Jul 27, 2013

@author: Divine
'''
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from listitems import NoteItemTitle, NoteContent, NoteItem, EditButton
from kivy.uix.screenmanager import RiseInTransition
from kivy.weakreflist import WeakList
from kivy.animation import Animation
from weakref import ref, proxy
from kivy.lang import Builder
from kivy.clock import Clock
from uiux import Screen_
            
class ListScreenItemTitle(NoteItemTitle):
    height_hint = 0.088
    
class ActionListItemTitle(NoteItemTitle):
    height_hint = (2.0/15.0)
    
class ContentMajor(NoteContent):
    height_hint = (322./1136.)

class ContentMinor(NoteContent):
    height_hint = (190./1136.)

class ListScreenItem(NoteItem):
    pass

class ActionListItem(NoteItem):
    pass

class ListScreen(Screen_):
    action_view_item = ObjectProperty(proxy(ActionListItem))
    _item = ObjectProperty(proxy(ListScreenItem))
    action_view = ObjectProperty(None)
    action_items = ListProperty([])
    list_items = ListProperty([])
    page = StringProperty('')
    page_number = NumericProperty(None)
    selection = ListProperty([])
    
    def __init__(self, **kwargs):
        self.register_event_type('on_what')
        self.register_event_type('on_drop')
        self.register_event_type('on_archive')
        self.register_event_type('on_comments')
        self.register_event_type('on_new_item')
        self.register_event_type('on_due_date')
        self.register_event_type('on_importance')
        super(ListScreen, self).__init__(**kwargs)
        
    def on_list_view(self, instance, value):
        if value:
            super(ListScreen, self).on_list_view(instance, value)
            ListScreenItemTitle.screen = ContentMinor.screen = EditButton.screen = instance.proxy_ref
            ListScreenItemTitle.listview = value
        
    def on_action_view(self, instance, value):
        if value:
            ActionListItemTitle.screen = ContentMajor.screen = instance.action_view_item.screen = instance.proxy_ref
            ActionListItemTitle.listview = instance.action_view_item.listview = value
            ListScreenItemTitle.drop_zones = [value, instance.list_view]
            ActionListItemTitle.drop_zones = [value,]

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
                del i

            self.list_items, self.action_items = list_items, action_items
            del list_items, action_items

    def _args_converter(self, row_index, an_obj):
        _dict = {}
        _dict['ix'], _dict['text'], _dict['when'], _dict['why'], _dict['how'] = an_obj
        _dict['why'] = bool(_dict['why'])

        if _dict['ix'] < 4:

            if not _dict['text']:
                _dict['text'] = 'Drag a Task here.'
                _dict['disabled'] = True

        del an_obj
        return _dict

    def on_new_item(self, instance, text):
        text = text.lstrip()

        if text:
            #Mimic `ListAdapter.create_view`
            listview = self.list_view.proxy_ref
            data = (9e9, text, u"", 0, u"")
            index = len(self.list_items)
            item_args = self._args_converter(index, data)
            item_args.update({'index': index})#, 'listview': listview})
            new_item = listview.cached_views[index] = self.accordion_view_item(**item_args)
            #new_item.bind(on_release=listview.handle_selection)
            listview.container.add_widget(new_item)

            def _on_start(a, w):
                instance.text = ''
                instance.focus = False

            def _on_complete(a, w):
                cursor = w.root_directory.cursor()
                cursor.execute("""
                               INSERT INTO [notebook](ix, what, page)
                               VALUES((SELECT MAX(ROWID) FROM [notebook])+1, ?, ?);
                               
                               SELECT MAX(ROWID) FROM [notebook];
                               """,
                               (text, w.page))
                ix = cursor.fetchall()[0][0]
                new_item.ix = ix
                self.list_items.append((ix, text, u"", 0, u""))

            _anim = Animation(y=0, t='out_expo', d=0.3)
            _anim.bind(on_start=_on_start, on_complete=_on_complete)
            instance._anim = ref(_anim)
            _anim.start(self.proxy_ref)

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
        self.polestar = lambda : None
        self.dispatch('on_pre_enter')

    def on_complete(self, instance):
        cursor = self.root_directory.cursor()
        ix = instance.parent.ix

        cursor.execute("""
                       INSERT INTO [archive]
                       SELECT * FROM [notebook] WHERE ix=? and page=?;
                       """,
                       (ix, self.page))
        self.polestar = lambda : None
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
            instance.screen.opacity = 0.5
            dtms = self.manager.get_screen('Date-Time Mini-Screen')
            dtms.item = instance
            kwargs = {'duration': 0.2}
            self.dispatch('on_screen_change', 'Date-Time Mini-Screen', kwargs, RiseInTransition)

    def on_drop(self, items):
        if items:
            cursor = self.root_directory.cursor()
            cursor.executemany("""
                               UPDATE [notebook]
                               SET what=?, when_=?, why=?, how=?
                               WHERE ix=? AND page=?;
                               """,
                               items)
            self.dispatch('on_pre_enter')
        del items

    def on_archive(self, *args):
        screen = self.manager.get_screen('Archive Screen')
        screen.page, screen.page_number = self.page, self.page_number
        kwargs = {'direction': 'left', 'duration': 0.2}
        self.dispatch('on_screen_change', 'Archive Screen', kwargs)
        del screen, kwargs

Builder.load_string("""
#:import NavBar uiux.NavBar
#:import NewItemWidget uiux.NewItemWidget
#:import WeakMethod kivy.weakmethod.WeakMethod
#:import ActionListView listviews.ActionListView
#:import DoubleClickButton uiux.DoubleClickButton
#:import AccordionListView listviews.AccordionListView

<-ActionListItemTitle>:
    label: label_id
    layout: layout_id
    font_size: self.width*0.062

    FloatLayout:
        id: layout_id
        size: root.size
        pos: root.pos
        canvas.before:
            Color:
                rgba: root.state_color
            Rectangle:
                size: self.size
                pos: self.pos

        Label:
            text: 'L' if self.disabled else ('-' if root.parent.collapse_alpha==0.0 else '+')
            size_hint: 0.1, 1
            pos_hint: {'x': 0, 'y': 0}
            font_size: self.width*0.6
            font_name: 'heydings_icons.ttf'
            color: root.text_color
            disabled_color: self.color
        Label:
            id: label_id
            text: root.text
            size_hint: 0.9, 1
            pos_hint: {'x': 0.1, 'y': 0}
            font_size: root.font_size
            font_name: root.font_name
            shorten: root.shorten
            color: root.text_color
            markup: root.markup
            disabled_color: self.color
            text_size: (self.size[0]-(0.1*self.size[0]), None) if root.aleft else (None, None)

<ContentMajor>:
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos

    DoubleClickButton:
        size_hint: 0.9, 0.25
        pos_hint: {'center_x': 0.5, 'center_y': 0.8333}
        icon_text: '!'
        text: 'IMPORTANT'
        font_size: self.width*0.07
        text_color: app.blue if self.double_click_switch else app.dark_gray
        double_click_switch: root.why
        #on_double_click_switch: root.dispatch('on_importance', *args)
    DoubleClickButton:
        size_hint: 0.9, 0.25
        pos_hint: {'center_x': 0.5, 'center_y': 0.6}
        icon_text: 'T'
        text: root.when
        font_size: self.width*0.07
        text_color: root.text_color
        #on_double_click_switch: root.screen.dispatch('on_due_date', root.parent, args[1])
    Label:
        id: icon_id
        text: 'e'
        font_name: 'breezi_font-webfont.ttf'
        font_size: self.height*0.7
        color: root.text_color
        size_hint: None, 0.25
        pos_hint: {'x': 0.05, 'center_y': 0.3}
        width: self.height
        text_size: self.size[0], None
    EditButton:
        text: root.how
        max_chars: 70
        size_hint: 0.75, 0.3
        top: icon_id.top
        x: icon_id.right
        font_name: 'Walkway Bold.ttf'
        #font_size: self.width*0.053
        font_size: self.width*0.07
        text_color: root.text_color

<ContentMinor>:
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
        #on_double_click_switch: root.screen.dispatch('on_due_date', root.parent, args[1])
    DoubleClickButton:
        size_hint: 0.1, 0.3
        pos_hint: {'x': 0.85, 'top': 1}
        icon_text: '!'
        text: ''
        font_size: root.width*0.07
        #font_size: self.height*0.421875
        text_color: app.blue if self.double_click_switch else app.dark_gray
        double_click_switch: root.why
        #on_double_click_switch: root.dispatch('on_importance', *args)
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

<ListScreenItem>:
    title: title_id
    content: content_id
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))
    shadow_color: app.dark_blue if title_id.state=='dragged' else (app.blue if title_id.state=='down' else app.no_color)
    text_color: app.dark_blue if (self.collapse_alpha==0.0 or title_id.state=='down') else (app.blue if title_id.state=='dragged' else app.dark_gray)
    state_color: app.no_color if title_id.state=='dragged' else app.smoke_white

    ListScreenItemTitle:
        id: title_id
        text: root.text
        shorten: True
        x: root.x
        top: root.top
        width: root.width
        font_size: self.width*0.07
        text_color: root.text_color
        state_color: root.state_color
        height: self.height_hint*root.screen.height
    ContentMinor:
        id: content_id
        why: root.why
        how: root.how
        when: root.when
        x: root.x
        top: title_id.y
        width: root.width
        text_color: root.text_color
        state_color: root.state_color
        height: root.screen.height*self.height_hint

<ActionListItem>:
    title: title_id
    content: content_id
    shadow_color: app.shadow_gray
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))
    state_color: app.no_color if title_id.state=='dragged' else (app.light_blue if title_id.state=='down' else app.white)
    text_color: app.dark_gray if self.disabled else app.dark_blue

    ActionListItemTitle:
        id: title_id
        text: root.text
        x: root.x
        top: root.top
        width: root.width
        text_color: root.text_color
        state_color: root.state_color
        height: self.height_hint*root.screen.height
    ContentMajor:
        id: content_id
        why: root.why
        how: root.how
        when: root.when
        x: root.x
        top: title_id.y
        width: root.width
        text_color: root.text_color
        state_color: root.state_color
        height: root.screen.height*self.height_hint

<ListScreen>:
    name: 'List Screen'
    list_view: list_view_id
    action_view: action_view_id

    NavBar:
        id: navbar_id
        text: root.page
        size_hint: 1, 0.1127
        #font_size: root.width*0.28
        font_size: root.width*0.1
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
        pos_hint: {'x': 0, 'top': 0.8873}
        height: 0.4*root.height
        #top: navbar_id.y
        list_item: root.action_view_item
        args_converter: root._args_converter
        data: root.action_items
    AccordionListView:
        id: list_view_id
        size_hint: 1, 0.4
        top: action_view_id.y
        list_item: root._item
        args_converter: root._args_converter
        data: root.list_items
    NewItemWidget:
        hint_text: 'Create New Task...'
        size_hint: 1, 0.086
        pos_hint: {'y': 0}
        on_text_validate: root.dispatch('on_new_item', *args[1:])
""")

