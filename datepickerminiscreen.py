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
    
    def _set_date(self, value, timedelta=datetime.timedelta):
        ravel = itertools.chain.from_iterable
        today = datetime.date.today()

        def _args_converter(date_cursor, delta):
            date_label = Day(text=str(date_cursor.day))

            if date_cursor < today:
                date_label.disabled = True
            elif ((delta < 0) or (value.month <> date_cursor.month)):
                date_label.in_month = False

            return date_label

        #self.title.text = self.month_names[value.month-1] + str(value.year)
        self.year, self.month = value.year, value.month
        date = datetime.date(value.year, value.month, 1)
        dt = date.isoweekday()# - instance.type_of_calendar
        cached_views = self.body.cached_views

        for child in cached_views.itervalues():
            child.title.clear_widgets()

        these = ravel(itertools.repeat(i, 7) for i in sorted(cached_views.itervalues(), key=cached_views.get))
        those = (_args_converter((date+timedelta(days=delta)), delta) for delta in xrange(-dt, ((7*6)-dt)))
        _on_release = lambda *_: self.body.handle_selection

        for this, that in itertools.izip(these, those):
            that.bind(on_release=_on_release(that))
            that.week = this
            this.title.add_widget(that)

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

    def on_today(self, instance, *args):
        instance.dispatch('on_deselect')
        instance.date = daetime.date.today()

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
                on_press: root.previous_month()
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
                on_press: root.next_month()

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
