from kivy.properties import AliasProperty, BooleanProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty
from uiux import Selectable, Clickable, Editable, Completable, Deletable, DragNDroppable, AccordionListItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.utils import escape_markup
from kivy.lang import Builder
from kivy.clock import Clock

class PagesScreenItem(Clickable, Deletable, Editable):
    page_number = NumericProperty(-1)
    screen = ObjectProperty(None)
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'edit', 'normal'))

    def on_text_validate(self, instance):
        if super(PagesScreenItem, self).on_text_validate(instance, instance.text):
            _l = lambda *_: self.screen.dispatch('on_what', self, instance.text)
            Clock.schedule_once(_l, 0.25)

    def on_touch_down(self, touch):
        if ((self.collide_point(*touch.pos)) or (self.state == 'edit')):
            return super(PagesScreenItem, self).on_touch_down(touch)
        elif self.state <> 'normal':
            self.state = 'normal'
            return True

class NoteItemTitle(Clickable, Completable, Deletable, DragNDroppable, Editable):
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'dragged', 'edit', 'normal'))
    screen = ObjectProperty(None)
    
    def _get_listview(self):
        return self.parent.listview
        
    listview = AliasProperty(_get_listview, None)
    
    def on_hold_down(self, *args):
        if self.parent.is_selected:
            self.hold_time = 0.0
            return False
        else:
            return super(NoteItemTitle, self).on_hold_down(*args)

    def on_touch_down(self, touch):
        if ((self.collide_point(*touch.pos)) or (self.state == 'edit')):
            return super(NoteItemTitle, self).on_touch_down(touch)
        elif self.state <> 'normal':
            self.state = 'normal'
            return True

    def on_text_validate(self, instance):
        if super(NoteItemTitle, self).on_text_validate(instance, instance.text):
            _l = lambda *_: self.screen.dispatch('on_what', self.parent, instance.text)
            Clock.schedule_once(_l, 0.25)

    def on_drag(self, instance, *args):
        instance = instance.parent
        super(NoteItemTitle, self).on_drag(instance, *args)
        
    def on_drop(self, instance, *args):
        instance = instance.parent
        super(NoteItemTitle, self).on_drop(instance, *args)
        
    def on_return(self, instance, *args):
        instance = instance.parent
        super(NoteItemTitle, self).on_return(instance, *args)

class ArchiveScreenItemTitle(Deletable, Clickable):
    screen = ObjectProperty(None)
    state = OptionProperty('normal', options=('delete', 'down', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.state <> 'normal':
                self.state = 'normal'
            return True

        else:
            return super(ArchiveScreenItemTitle, self).on_touch_down(touch)

class NoteItem(AccordionListItem):
    how = StringProperty('')
    when = StringProperty('')
    ix = NumericProperty(None)
    why = BooleanProperty(False)
    screen = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_comments')
        self.register_event_type('on_importance')
        super(NoteItem, self).__init__(**kwargs)

        self.title.aleft = kwargs['aleft']

    def on_comments(self, *args):#instance, value):
        print args
        value = value.lstrip()
        #instance.focus = False

        if self.how <> value:
            _l = lambda *_: self.screen.dispatch('on_comments', self, value)
            Clock.schedule_once(_l, 0.25)

    def on_importance(self, instance, value):
        if self.why <> value:
            _l = lambda *_: self.screen.dispatch('on_importance', self, value)
            Clock.schedule_once(_l, 0.25)

class ListScreenItem(NoteItem):

    def __init__(self, **kwargs):
        super(ListScreenItem, self).__init__(**kwargs)
        self.title.drop_zones = kwargs['drop_zones']

class ActionListItem(NoteItem):

    def __init__(self, **kwargs):
        super(ActionListItem, self).__init__(**kwargs)
        self.title.drop_zones = kwargs['drop_zones']

class ArchiveScreenItem(NoteItem):
    pass

class QuickViewScreenItemTitle(Completable, Deletable):
    state = OptionProperty('normal', options=('complete', 'delete', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.state <> 'normal':
                self.state = 'normal'
            return True

        else:
            return super(QuickViewScreenItemTitle, self).on_touch_down(touch)

class QuickViewScreenItem(BoxLayout):
    ix = NumericProperty(None)
    text = StringProperty('')
    when = StringProperty('', allownone=True)
    why = BooleanProperty(False)
    how = StringProperty('', allownone=True)
    markup = BooleanProperty(False)
    screen = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(QuickViewScreenItem, self).on_touch_down(touch)

class Week(AccordionListItem):
    screen = ObjectProperty(None)
    title_height_hint = NumericProperty(0.0)
    content_height_hint = NumericProperty(0.0)

class ContentMajor(FloatLayout):
    state_color = ListProperty([])
    text_color = ListProperty([])
    screen = ObjectProperty(None)
    when = StringProperty('')
    why = BooleanProperty(False)
    how = StringProperty('')

    def __init__(self, **kwargs):
        self.register_event_type('on_comments')
        self.register_event_type('on_importance')
        super(ContentMajor, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super(ContentMajor, self).on_touch_down(touch)
        else:
            return False

    def on_importance(self, *args):
        pass

    def on_comments(self, *args):
        print args

Builder.load_string("""
#:import EditButton uiux.EditButton
#:import DoubleClickButton uiux.DoubleClickButton

<PagesScreenItem>:
    aleft: True
    shorten: True
    font_size: self.width*0.0421875
    height: self.screen.height*0.088
    state_color: app.no_color if self.state == 'down' else app.white
    on_release: self.screen.dispatch('on_selected_page', args[0].text, args[0].page_number)
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.y, self.right, self.y
            width: 1.0

<-ActionListItemTitle@NoteItemTitle, -ArchiveScreenItemTitle>:
    label: label_id
    layout: layout_id
    font_size: self.width*0.0421875

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
        font_size: self.width*0.05
        text_color: app.blue if self.double_click_switch else app.dark_gray
        double_click_switch: root.why
        on_double_click_switch: root.dispatch('on_importance', *args)
    DoubleClickButton:
        size_hint: 0.9, 0.25
        pos_hint: {'center_x': 0.5, 'center_y': 0.6}
        icon_text: 'T'
        text: root.when
        font_size: self.width*0.05
        text_color: root.text_color
        on_double_click_switch: root.screen.dispatch('on_due_date', root.parent, args[1])
    Label:
        id: icon_id
        text: 'e'
        font_name: 'breezi_font-webfont.ttf'
        font_size: self.height*0.421875
        color: root.text_color
        size_hint: None, 0.25
        pos_hint: {'x': 0.05, 'center_y': 0.3}
        width: self.height
        text_size: self.size[0], None
    EditButton:
        text: root.how
        size_hint: 0.75, 0.3
        top: icon_id.top
        x: icon_id.right
        font_name: 'Walkway Bold.ttf'
        font_size: self.width*0.053
        text_color: root.text_color
        screen: root.screen
        on_text_validate: root.dispatch('on_comments', *args)

<-ContentMinor@ContentMajor>:
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos

    DoubleClickButton:
        size_hint: 0.5, 0.3
        pos_hint: {'x': 0.05, 'top': 1}
        icon_text: 'Due:'
        icon_font_name: 'Walkway Bold.ttf'
        font_size: root.width*0.04
        text: root.when
        text_color: root.text_color
        on_double_click_switch: root.screen.dispatch('on_due_date', root.parent, args[1])
    DoubleClickButton:
        size_hint: 0.1, 0.3
        pos_hint: {'x': 0.85, 'top': 1}
        icon_text: '!'
        text: ''
        font_size: root.width*0.05
        #font_size: self.height*0.421875
        text_color: app.blue if self.double_click_switch else app.dark_gray
        double_click_switch: root.why
        on_double_click_switch: root.dispatch('on_importance', *args)
    Label:
        id: icon_id
        text: 'Notes:'
        font_name: 'Walkway Bold.ttf'
        #font_size: self.height*0.421875
        font_size: root.width*0.035
        color: root.text_color
        size_hint: 0.11, 0.3
        disabled_color: self.color
        pos_hint: {'x': 0.05, 'top': 0.5}
        text_size: self.size
        valign: 'top'
    EditButton:
        text: root.how
        size_hint: 0.8, 0.5
        top: icon_id.top
        x: icon_id.right
        font_name: 'Walkway Bold.ttf'
        font_size: root.width*0.035
        text_color: root.text_color
        screen: root.screen
        on_text_validate: root.parent.dispatch('on_comments', *args)
   
<ListScreenItem>:
    title: title_id
    content: content_id
    text_color: app.blue if (self.collapse_alpha==0.0 or title_id.state=='dragged') else app.dark_gray
    state_color: app.no_color if self.state=='dragged' else app.smoke_white
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))

    NoteItemTitle:
        id: title_id
        text: root.text
        shorten: True
        size_hint: 1, None
        pos_hint: {'x': 0, 'top': 1}
        screen: root.screen
        font_size: self.width*0.043
        text_color: root.text_color
        state_color: root.state_color
        on_release: root.listview.handle_selection(root)
        height: self.screen.height*root.title_height_hint
    ContentMinor:
        id: content_id
        why: root.why
        how: root.how
        when: root.when
        top: title_id.y
        pos_hint: {'x': 0}
        size_hint: 1, None
        screen: root.screen
        text_color: root.text_color
        state_color: root.state_color
        height: root.screen.height*root.content_height_hint
        #on_comments: print args
        on_importance: root.dispatch('on_importance', root, args[2])

<ActionListItem>:
    title: title_id
    content: content_id
    state_color: app.no_color if title_id.state=='dragged' else (app.light_blue if title_id.state=='down' else app.white)
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))
    text_color: app.dark_gray if self.disabled else app.blue

    ActionListItemTitle:
        id: title_id
        text: root.text
        size_hint: 1, None
        pos_hint: {'x': 0, 'top': 1}
        screen: root.screen
        font_size: (self.height*0.3)
        text_color: root.text_color
        state_color: root.state_color
        on_release: root.listview.handle_selection(root)
        height: root.screen.height*root.title_height_hint
    ContentMajor:
        id: content_id
        why: root.why
        how: root.how
        when: root.when
        top: title_id.y
        pos_hint: {'x': 0}
        size_hint: 1, None
        screen: root.screen
        text_color: root.text_color
        state_color: root.state_color
        height: root.screen.height*root.content_height_hint
        on_comments: print args
        on_importance: root.dispatch('on_importance', root, args[2])

<ArchiveScreenItem>:
    title: title_id
    content: content_id
    size_hint: 1, None
    state_color: app.no_color if title_id.state in ('down', 'dragged') else app.white
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))
    text_color: app.blue

    ArchiveScreenItemTitle:
        id: title_id
        text: root.text
        size_hint: 1, None
        pos_hint: {'x': 0, 'top': 1}
        screen: root.screen
        font_size: (self.height*0.3)
        text_color: root.text_color
        state_color: root.state_color
        on_release: root.listview.handle_selection(root)
        height: root.screen.height*root.title_height_hint
    ContentMinor:
        id: content_id
        disabled: True
        why: root.why
        how: root.how
        when: root.when
        top: title_id.y
        pos_hint: {'x': 0}
        size_hint: 1, None
        screen: root.screen
        text_color: root.text_color
        state_color: root.state_color
        height: root.screen.height*root.content_height_hint

<-QuickViewScreenItemTitle>:
    label: label_id
    layout: layout_id
    font_size: (self.height*0.421875)
    state_color: app.smoke_white
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos

    FloatLayout:
        id: layout_id
        size: root.size
        pos: root.pos

        BoxLayout:
            spacing: 5
            pos_hint: {'center_x': .5, 'center_y': .5}
            size_hint: 0.9, .75
            
            Label:
                id: label_id
                text: root.text
                font_size: root.font_size
                font_name: root.font_name
                shorten: root.shorten
                color: root.text_color
                markup: root.markup
                text_size: (self.size[0], None) if root.aleft else (None, None)
                canvas.after:
                    Color:
                        rgba: app.shadow_gray
                    Line:
                        points: self.parent.x, self.y, self.right, self.y


<QuickViewScreenItem>:
    orientation: 'vertical'
    padding: 10
    spacing: 5
    state: title_id.state

    QuickViewScreenItemTitle:
        id: title_id
        text: root.text
        screen: root.screen
        size_hint: 1, .4
        aleft: True
        markup: root.markup

    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.9
        spacing: 10

        Label:
            size_hint: 0.8, 1
            text: root.how
            valign: 'top'
        BoxLayout:
            orientation: 'vertical'
            size_hint: 0.2, .6
            pos_hint: {'top' : 0.9}

            Label:
                size_hint: 1, .75
                text: '2 Days'
                font_size: (self.height*0.421875)
                canvas.before:
                    Color:
                        rgba: app.blue
                    Rectangle:
                        size: self.size
                        pos: self.pos
            Label:
                text: '11.06.2013'
                size_hint: 0.75, 0.25
                pos_hint: {'center_x' : .5}
                color: app.dark_gray

<Week>:
    title: title_id
    content: content_id
    shadow_color: app.no_color
    height: title_id.height + (content_id.height*(1-self.collapse_alpha))

    GridLayout:
        id: title_id
        cols: 7
        rows: 1
        size_hint: 1, None
        height: root.screen.height*root.title_height_hint
        pos_hint: {'top': 1, 'x': 0}
    DayDropDown:
        id: content_id
        size_hint: 1, None
        height: 83 + (1.0/3.0)
        top: title_id.y
""")
