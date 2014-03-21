from kivy.properties import ObjectProperty, AliasProperty, ListProperty, NumericProperty
import datetime, math, itertools
from datetimewidgets import Day
from kivy.lang import Builder
from uiux import Screen_

class DateTimeMiniScreen(Screen_):
    day = NumericProperty(0)
    year = NumericProperty(1)
    month = NumericProperty(1)
    item = ObjectProperty(None)
    body = ObjectProperty(None)
    time = ObjectProperty(datetime.time(12, 00))
    month_names = ListProperty(('January ', 'February ', 'March ', 'April ', 'May ', 'June ', 'July ', 'August ', 'September ', 'October ', 'November ', 'December '))

    def _get_date(self):
        if self.day:
            day = self.day
        else:
            day = 1

        return datetime.date(self.year, self.month, day)
    
    def _set_date(self, date):
        self.body.dispatch('on_populated', self)

    date = AliasProperty(_get_date, _set_date)#, bind=('size', 'pos'))

    def _get_when(self):
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

    when = AliasProperty(_get_when, _set_when)
    
    def __init__(self, **kwargs):
        self.register_event_type('on_today')
        self.register_event_type('on_deselect')
        self.register_event_type('on_next_month')
        self.register_event_type('on_previous_month')
        super(DateTimeMiniScreen, self).__init__(**kwargs)

    def on_item(self, instance, value):
        if self.item:

            if self.item.when:
                self.when = self.item.when
            else:
                #For the timing between sizing and populating days in calendar?
                self.when = datetime.date.today().isoformat() + 'T12:00'

    def _args_converter(self, i, _):
        return {'index': i,
                'size_hint_y': None,
                'title_height': self.height/6.0,
                'content_height': self.height/6.0,
                'listview': self}

    def on_deselect(self, *args):
        self.body.deselect_all()
    
    def on_next_month(self, instance, maxyear=datetime.MAXYEAR):
        self.dispatch('on_deselect')

        if self.date.month == 12:
            new_year = self.date.year + 1

            if new_year <= maxyear:
                self.date = datetime.date(new_year, 1, self.date.day)

        else:
            self.date = datetime.date(self.date.year, self.date.month + 1, self.date.day)

    def on_previous_month(self, instance, today=datetime.date.today()):
        self.dispatch('on_deselect')

        if self.date.month == 1:
            new_date = datetime.date(self.date.year - 1, 12, self.date.day)
        else:
            new_date = datetime.date(self.date.year, self.date.month - 1, self.date.day)

        if ((new_date.month >= today.month) and (new_date.year >= today.year)):
            self.date = new_date

    def on_today(self, *args):
        self.dispatch('on_deselect')
        self.date = daetime.date.today()

Builder.load_string("""
#:import NavBar uiux
#:import Week listitems.Week
#:import Button_ uiux.Button_
#:import AccordionListView listviews.AccordionListView

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
    root_directory: app.db

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
                font_size: self.height*0.7
                on_press: root.dispatch('previous_month', *args)
            Label:
                id: title_id
                color: app.white
                font_name: 'Walkway Bold.ttf'
                font_size: self.height*0.421875
                text: root.month_names[root.month-1] + str(root.year)
            Button_:
                text: '>'
                size_hint: None, 1
                width: self.height
                font_size: self.height*0.7
                on_press: root.dispatch('next_month', *args)

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

    AccordionListView:
        id: body_id
        spacing: 0
        list_item: Week
        size_hint: 1, 0.4
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
