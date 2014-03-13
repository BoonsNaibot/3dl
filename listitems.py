from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty, OptionProperty, AliasProperty
from uiux import Selectable, Clickable, Editable, Completable, Deletable, TouchDownAndHoldable, AccordionListItem
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.utils import escape_markup
from kivy.lang import Builder
from kivy.clock import Clock

class PagesScreenItem(Clickable, Deletable, Editable):
    index = NumericProperty(-1)
    screen = ObjectProperty(None)
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'edit', 'normal'))

    def on_release(self):
        self.screen.dispatch('on_selected_page', self.text, self.index)

    def on_text_validate(self, instance):
        if super(PagesScreenItem, self).on_text_validate(instance, instance.text):
            _l = lambda *_: self.screen.dispatch('on_what', self, instance.text)
            Clock.schedule_once(_l, 0.25)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            nruter = self.state == 'normal'

            if not nruter:
                self.state = 'normal'
            
            return not nruter
        else:
            return super(PagesScreenItem, self).on_touch_down(touch)

class NoteItemTitle(Clickable, Completable, Deletable, TouchDownAndHoldable, Editable):
    state = OptionProperty('normal', options=('complete', 'delete', 'down', 'dragged', 'edit', 'normal'))
    screen = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            nruter = self.state == 'normal'

            if not nruter:
                self.state = 'normal'
            
            return not nruter
        else:
            return super(NoteItemTitle, self).on_touch_down(touch)

    def on_text_validate(self, instance):
        if super(NoteItemTitle, self).on_text_validate(instance, instance.text):
            _l = lambda *_: self.screen.dispatch('on_what', self.parent, instance.text)
            Clock.schedule_once(_l, 0.25)

class NoteItem(AccordionListItem):
    how = StringProperty('')
    ix = NumericProperty(None)
    why = BooleanProperty(False)
    screen = ObjectProperty(None)
    drag_opacity = NumericProperty(0.75)

    def __init__(self, **kwargs):
        self.register_event_type('on_comments')
        self.register_event_type('on_importance')
        super(NoteItem, self).__init__(**kwargs)

        self.title.droppable_zone_objects = kwargs['droppable_zone_objects']
        self.title.aleft = kwargs['aleft']
        self.title.font_name = kwargs['font_name']

    def on_comments(self, instance, value):
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
    pass

class ActionListItem(ListScreenItem):
    pass
    '''def on_state(self, instance, value):
        if value in ('normal', 'down'):
            if not instance.is_selected:
                instance.markup = True
                instance.label.text = "[font='heydings_icons.ttf'][color=ffffff]- [/color][/font]" + escape_markup(instance.text)
        else:
            instance.label.text = instance.text'''

class QuickViewScreenItemTitle(Completable, Deletable):
    state = OptionProperty('normal', options=('complete', 'delete', 'dragged', 'edit', 'normal'))

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

            if self.state == 'normal':
                return False
            else:
                self.state = 'normal'
                return True

        else:
            return super(QuickViewScreenItem, self).on_touch_down(touch)

class ArchiveScreenItemTitle(Deletable, Clickable):
    state = OptionProperty('normal', options=('delete', 'down', 'normal'))

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        else:
            return super(ArchiveScreenItemTitle, self).on_touch_down(touch)

class ArchiveScreenItem(AccordionListItem):
    pass

class Week(AccordionListItem):
    title_height = NumericProperty(0.0)
    content_height = NumericProperty(0.0)

Builder.load_string("""
#:import DoubleClickButton uiux.DoubleClickButton
#:import EditButton uiux.EditButton

<PagesScreenItem>:
    aleft: True
    shorten: True
    height: self.screen.height*0.088
    state_color: app.gray if self.state == 'down' else app.white
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.y, self.right, self.y
            width: 1.0

<NoteItem>:
    title: title_id
    size_hint: 1, None
    text_color: app.blue
    state_color: app.no_color if title_id.state=='dragged' else app.white

    NoteItemTitle:
        id: title_id
        text: root.text
        size_hint: 1, None
        pos_hint: {'x': 0, 'top': 1}
        screen: root.screen
        text_color: root.text_color
        state_color: root.state_color
        on_release: root.listview.handle_selection(root)
        height: root.screen.height*root.title_height_hint
    
<ListScreenItem>:
    content: content_id
    text_color: app.blue
    height: self.title.height + (content_id.height*(1-self.collapse_alpha))

    BoxLayout:
        id: content_id
        orientation: 'vertical'
        size_hint: 1, None
        pos_hint: {'x': 0}
        top: root.title.y
        height: root.screen.height*root.content_height_hint
        canvas.before:
            Color:
                rgba: root.state_color
            Rectangle:
                size: self.size
                pos: self.pos

        DoubleClickButton:
            icon_text: '!'
            text: 'IMPORTANT'
            text_color: root.text_color
            double_click_switch: root.why
            opacity: 1.0 if self.double_click_switch else 0.5
            on_double_click_switch: root.dispatch('on_importance', *args)
        DoubleClickButton:
            icon_text: 'T'
            #text: root.when
            opacity: 1.0
            text_color: root.text_color
            on_double_click_switch: root.screen.dispatch('on_due_date', root, args[1])
        BoxLayout:
            size_hint: 0.5, 1
            pos_hint: {'center_x': 0.5}

            Label:
                id: icon_id
                text: 'b'
                font_name: 'breezi_font-webfont.ttf'
                size_hint: None, 1
                width: self.height
                color: root.text_color
                font_size: self.height*0.421875
            EditButton:
                text: root.how
                size_hint: None, 1                
                font_name: 'Walkway Bold.ttf'
                width: root.width - icon_id.width
                font_size: self.height*0.5
                #text_color root.text_color
                screen: root.screen
                on_text_validate: root.dispatch('on_comments', args[0], self.text)

<ActionListItem>:
    state_color: app.no_color if self.title.state=='dragged' else (app.blue if root.collapse_alpha==0.0 else (app.light_blue if self.title.state=='down' else app.gray))
    text_color: app.white if root.collapse_alpha==0.0 else app.dark_gray
    shadow_color: app.smoke_white

<ArchiveScreenItem>:
    aleft: True
    shorten: True
    height: self.screen.height*0.088
    state_color: app.smoke_white if self.state == 'down' else app.light_gray
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.x, self.y, self.right, self.y
            width: 1.0

<QuickViewScreenItemTitle>:
    label: self.label
    layout: layout_id
    label: label_id
    font_size: (self.height*0.421875)
    state_color: app.smoke_white
    canvas.before:
        Color:
            rgba: self.state_color
        Rectangle:
            size: self.size
            pos: self.pos
    canvas.after:
        Color:
            rgba: app.shadow_gray
        Line:
            points: self.layout.x, self.label.y, self.label.right, self.label.y

    FloatLayout:
        size: root.size
        pos: root.pos

        BoxLayout:
            id: layout_id
            orientation: 'horizontal'
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
        #height: root.listview.height/7.0
        height: 83 + (1.0/3.0)
    DayDropDown:
        id: content_id
        size_hint: 1, None
        height: 83 + (1.0/3.0)
        top: title_id.y
""")
