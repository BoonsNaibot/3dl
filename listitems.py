from kivy.properties import AliasProperty, BooleanProperty, ListProperty, NumericProperty, ObjectProperty, OptionProperty, StringProperty
from uiux import Selectable, Clickable, Editable, Completable, Deletable, DragNDroppable, AccordionListItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import escape_markup
from kivy.lang import Builder
from kivy.clock import Clock

class EditButton(Editable):
    
    def on_touch_down(self, touch):
        if ((self.collide_point(*touch.pos)) or (self.state == 'edit')):
            return super(EditButton, self).on_touch_down(touch)

    def on_text_validate(self, instance):
        text = instance.text.lstrip()
        self.text = text
        self.parent.dispatch('on_comments', text)

class PagesScreenItem(Clickable, Deletable, Editable):
    screen = None
    listview = None
    height_hint = (153./1136.)
    page_number = NumericProperty(-1)
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

    def on_release(self):
        self.screen.dispatch('on_selected_page', self.text, self.page_number)
            
class QuickViewScreenItemTitle(Completable, Deletable):
    screen = None
    state = OptionProperty('normal', options=('complete', 'delete', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            if self.state <> 'normal':
                self.state = 'normal'
                return True

        else:
            return super(QuickViewScreenItemTitle, self).on_touch_down(touch)

class QuickViewScreenItem(BoxLayout):
    screen = None
    listview = None
    how = StringProperty('')
    text = StringProperty('')
    when = StringProperty('')
    ix = NumericProperty(None)
    title = ObjectProperty(None)
    why = BooleanProperty(False)
    markup = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super(QuickViewScreenItem, self).__init__(**kwargs)
        QuickViewScreenItemTitle.screen = self.screen

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(QuickViewScreenItem, self).on_touch_down(touch)

class NoteItemTitle(Clickable, Completable, Deletable, DragNDroppable, Editable):
    aleft = True
    screen = None
    listview = None
    drop_zones = []
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'dragged', 'edit', 'normal'))

    def on_press(self, *args):
        if (self.state == 'down'):
            self.hold_time = 0.0
            Clock.schedule_interval(self.on_hold_down, 0.05)
    
    def on_hold_down(self, *args):
        if self.screen.selection:
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
        instance = instance.parent.__self__
        super(NoteItemTitle, self).on_drag(instance, *args)
        
    def on_drop(self, instance, *args):
        instance = instance.parent.__self__
        super(NoteItemTitle, self).on_drop(instance, *args)
        
    def on_return(self, instance, *args):
        instance = instance.parent.__self__
        super(NoteItemTitle, self).on_return(instance, *args)

    def on_release(self):
        self.listview.handle_selection(self.parent)

class NoteContent(FloatLayout):
    state_color = ListProperty([])
    text_color = ListProperty([])
    why = BooleanProperty(False)
    when = StringProperty('')
    how = StringProperty('')
    screen = None

    def __init__(self, **kwargs):
        self.register_event_type('on_comments')
        self.register_event_type('on_importance')
        super(NoteContent, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super(NoteContent, self).on_touch_down(touch)
        else:
            return False

    def on_importance(self, *args):
        self.parent.dispatch('on_importance', *args)

    def on_comments(self, *args):
        self.parent.dispatch('on_comments', *args)

class NoteItem(AccordionListItem):
    screen = None
    listview = None
    how = StringProperty('')
    when = StringProperty('')
    ix = NumericProperty(None)
    why = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type('on_comments')
        self.register_event_type('on_importance')
        super(NoteItem, self).__init__(**kwargs)

    def on_comments(self, value):
        if self.how <> value:
            _l = lambda *_: self.screen.dispatch('on_comments', self.proxy_ref, value)
            Clock.schedule_once(_l, 0.25)

    def on_importance(self, instance, value):
        if self.why <> value:
            _l = lambda *_: self.screen.dispatch('on_importance', self.proxy_ref, value)
            Clock.schedule_once(_l, 0.25)

class Week(AccordionListItem):
    screen = None
    listview = None
    text = StringProperty('')

Builder.load_string("""

<-EditButton>:
    label: label_id

    Label:
        id: label_id
        pos: root.pos
        text: root.text
        size: root.size
        font_size: root.font_size
        font_name: root.font_name
        shorten: root.shorten
        color: root.text_color
        disabled_color: self.color
        markup: root.markup
        text_size: self.size
        valign: 'top'

<PagesScreenItem>:
    aleft: True
    shorten: True
    font_size: self.width*0.07
    #height: self.screen.height*0.088
    height: self.screen.height*self.height_hint
    state_color: app.no_color if self.state == 'down' else app.white
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.y, self.right, self.y
            width: 1.0

<NoteItem>:
    canvas.after:
        Color:
            rgba: self.shadow_color
        Line:
            close: True
            points: self.x, self.y, self.right, self.y, self.right, self.top, self.x, self.top

<-QuickViewScreenItemTitle>:
    label: label_id
    layout: layout_id
    font_size: (self.height*0.421875)
    state_color: app.smoke_white

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

<QuickLabel@Label>
    disabled_color: self.color

<QuickViewScreenItem>:
    title: title_id
    orientation: 'vertical'
    padding: 10
    spacing: 5
    state: title_id.state
    height: self.screen.height*0.2958

    QuickViewScreenItemTitle:
        id: title_id
        text: root.text
        size_hint: 1, .4
        aleft: True
        markup: root.markup

    BoxLayout:
        orientation: 'horizontal'
        size_hint: 1, 0.9
        spacing: 10

        QuickLabel:
            size_hint: 0.8, 1
            text: root.how
            color: app.dark_gray
            text_size: self.size
            valign: 'top'
            font_size: self.width*0.0421875
        BoxLayout:
            orientation: 'vertical'
            size_hint: 0.2, .6
            pos_hint: {'top' : 0.9}

            QuickLabel:
                size_hint: 1, .75
                text: '2 Days'
                font_size: (self.height*0.421875)
                canvas.before:
                    Color:
                        rgba: app.blue
                    Rectangle:
                        size: self.size
                        pos: self.pos
            QuickLabel:
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
        x: root.x
        top: root.top
        width: root.width
    DayDropDown:
        id: content_id
        text: root.text
        x: root.x
        top: title_id.y
        width: root.width
        height: 83 + (1.0/3.0)
""")
