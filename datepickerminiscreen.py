from kivy.properties import ObjectProperty, AliasProperty, ListProperty, NumericProperty
from kivy.lang import Builder
from uiux import Screen_
import datetime

class DateTimeMiniScreen(Screen_):
    year = NumericProperty(1)
    month = NumericProperty(1)
    item = ObjectProperty(None)
    body = ObjectProperty(None)
    date = ObjectProperty(datetime.date.today())
    time = ObjectProperty(datetime.time(12, 00))
    month_names = ListProperty(('January ', 'February ', 'March ', 'April ', 'May ', 'June ', 'July ', 'August ', 'September ', 'October ', 'November ', 'December '))

    def _get_day(self):
        if self.body and self.body.selection:
            return int(self.body.selection[0].text)
            
    day = AliasProperty(_get_day, None, bind=('body',))

    """def _get_when(self):
        if self.day:
            dt = datetime.datetime.combine(self.date, self.time)
            return dt.isoformat()[:16]
        else:
            return ''

    def _set_when(self, when):
        if when:
            dt = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M")
            self.date = dt.date()
            self.time = dt.time()
        else:
            return False

    when = AliasProperty(_get_when, _set_when, bind=('day',))"""
    
    def __init__(self, **kwargs):
        self.register_event_type('on_today')
        self.register_event_type('on_deselect')
        self.register_event_type('on_next_month')
        self.register_event_type('on_previous_month')
        super(DateTimeMiniScreen, self).__init__(**kwargs)

    def on_pre_enter(self, *args):
        if self.item:
            dt = datetime.datetime.strptime(self.item.when, '%Y-%m-%dT%H:%M')
            self.date = dt.date()
            self.time = dt.time()

    def on_date(self, instance, date):
        self.body.dispatch('on_populated', instance)

    def _args_converter(self, i, _):
        return {'index': i,
                'screen': self,
                'size_hint_y': None,
                'listview': self.body,
                'title_height_hint': 1.0/15.0,
                'content_height_hint': self.height/6.0}

    def on_deselect(self, *args):
        self.body.deselect_all()
    
    def on_next_month(self, instance, maxyear=datetime.MAXYEAR):
        self.dispatch('on_deselect')

        if self.date.month == 12:
            new_year = self.date.year + 1

            if new_year <= maxyear:
                self.date = datetime.date(new_year, 1, 1)

        else:
            self.date = datetime.date(self.date.year, self.date.month + 1, 1)

    def on_previous_month(self, instance, today=datetime.date.today()):
        self.dispatch('on_deselect')

        if self.date.month == 1:
            new_date = datetime.date(self.date.year - 1, 12, 1)
        else:
            new_date = datetime.date(self.date.year, self.date.month - 1, 1)

        if ((new_date.month >= today.month) and (new_date.year >= today.year)):
            self.date = new_date

    def on_today(self, *args):
        self.dispatch('on_deselect')
        self.date = datetime.date.today()

Builder.load_string("""
#:import NavBar uiux
#:import Week listitems.Week
#:import Button_ uiux.Button_
#:import DatePickerListView listviews.DatePickerListView

<DayofTheWeek@Label>:
    font_name: 'Walkway Bold.ttf'
    color: app.blue
    font_size: self.height*0.7

<Foobuttons@Button_>:
    state_color: app.no_color
    text_color: app.blue

<DateTimeMiniScreen>:
    body: body_id
    name: 'Date-Time Mini-Screen'

    NavBar:
        id: navbar_id
        size_hint: 1, .0775
        pos_hint:{'top': 0.9648}

        BoxLayout:
            size_hint: .9, .9
            pos_hint: {'center_x': .5, 'center_y': .5}

            Button_:
                text: '<'
                size_hint: None, 1
                width: self.height
                font_size: self.height*0.9
                on_press: root.dispatch('on_previous_month', root)
            Label:
                id: title_id
                color: app.white
                font_name: 'Walkway Bold.ttf'
                #font_size: self.height*0.421875
                font_size: self.height*0.7
                text: root.month_names[root.month-1] + str(root.year)
            Button_:
                text: '>'
                size_hint: None, 1
                width: self.height
                font_size: self.height*0.9
                on_press: root.dispatch('on_next_month', root)

    BoxLayout:
        size_hint: 1, 0.05
        pos_hint: {'x': 0, 'top': 0.8873}

        DayofTheWeek:
            text: 'SUN'
        DayofTheWeek:
            text: 'MON'
        DayofTheWeek:
            text: 'TUE'
        DayofTheWeek:
            text: 'WED'
        DayofTheWeek:
            text: 'THU'
        DayofTheWeek:
            text: 'FRI'
        DayofTheWeek:
            text: 'SAT'

    DatePickerListView:
        id: body_id
        spacing: 0
        list_item: Week
        size_hint: 1, 0.8
        pos_hint: {'x': 0, 'top': 0.8373}
        args_converter: root._args_converter
        data: range(6)
    BoxLayout:
        pos_hint: {'x': 0, 'y': 0}
        size_hint: 1, 0.0789

        Foobuttons:
            text: 'Cancel'
        Foobuttons:
            text: 'Today'
            on_press: root.dispatch('on_today', *args)
        Foobuttons:
            text: 'Submit'

""")
