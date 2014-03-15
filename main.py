from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
#kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import NoTransition
from kivy.properties import ObjectProperty, ListProperty

from apsw import Connection, SQLITE_OPEN_READWRITE, CantOpenError
#from kivy.modules import inspector
#from kivy.core.window import Window

kv = """
#:import ListScreen listscreen.ListScreen
#:import PagesScreen pagesscreen.PagesScreen
#:import QuickViewScreen quickviewscreen.QuickViewScreen
#:import ScreenManager kivy.uix.screenmanager.ScreenManager

<Application>:
    manager: manager_id

    ScreenManager:
        id: manager_id
        size: root.size
        pos: root.pos

        PagesScreen:
            root_directory: app.db
        QuickViewScreen:
            root_directory: app.db
        ListScreen
            root_directory: app.db
        

"""

class Application(Widget):
    manager = ObjectProperty(None)

class ThreeDoListApp(App):
    """Special Thanks to Joe Jimenez of Breezi[dot]com for breezi_font-webfont.ttf""" 
    ### Colors ###
    no_color = ListProperty((1.0, 1.0, 1.0, 0.))
    light_blue = ListProperty((0.498, 0.941, 1.0, 1.0))
    blue = ListProperty((0.0, 0.824, 1.0, 1.0))
    dark_blue = ListProperty((0.004, 0.612, 0.7412, 1.0))
    red = ListProperty((1.0, 0.549, 0.5294, 1.0))
    purple = ListProperty((0.451, 0.4627, 0.561, 1.0))
    white = ListProperty((1.0, 1.0, 1.0, 1.0))
    light_gray = ListProperty((1.0, 0.98, 0.941, 1.0))
    smoke_white = ListProperty((0.95, 0.97, 0.973, 1.0))
    gray = ListProperty((0.9137, 0.933, 0.9451, 1.0))
    dark_gray = ListProperty((0.533, 0.533, 0.533, 1.0))
    shadow_gray = ListProperty((0.8, 0.8, 0.8, 1.0))
    
    
    #preferences = ObjectProperty(JsonStore('preferences.json'))
    try:
        db = ObjectProperty(Connection('~/Documents/ThreeDoList/db.db', flags=SQLITE_OPEN_READWRITE))
    except CantOpenError:
        db = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_pre_start')
        super(ThreeDoListApp, self).__init__(**kwargs)

        if not self.db:
            connection = Connection(self.user_data_dir + '/' + self.name + '/db.db')
            cursor = connection.cursor()
            cursor.execute("""
                            CREATE TABLE [table of contents](
                            page_number INTEGER PRIMARY KEY,
                            page TEXT NOT NULL,
                            bookmark INTEGER DEFAULT 0);
                            
                            CREATE TABLE [notebook](
                            what TEXT DEFAULT '',
                            when_ TEXT DEFAULT '',
                            why INTEGER DEFAULT 0,
                            how TEXT DEFAULT '',
                            ix INTEGER,
                            FOREIGN KEY(page_number) REFERENCES [table of contents](page_number) ON UPDATE CASCADE);

                            CREATE TABLE [archive](
                            what TEXT,
                            when_ TEXT,
                            why INTEGER DEFAULT 0,
                            how TEXT,
                            FOREIGN KEY(page_number) REFERENCES [table of contents](page_number) ON UPDATE CASCADE);

                            CREATE TRIGGER [on_new_page]
                            AFTER INSERT ON [table of contents]
                            BEGIN
                                INSERT INTO notebook(bookmark, page_number, ix) VALUES(0, new.page_number, 1);
                                INSERT INTO notebook(bookmark, page_number, ix) VALUES(0, new.page_number, 2);
                                INSERT INTO notebook(bookmark, page_number, ix) VALUES(0, new.page_number, 3);
                            END;

                            CREATE TRIGGER [on_delete_page]
                            BEFORE DELETE ON [table of contents]
                            BEGIN
                                DELETE FROM notebook WHERE page_number=old.page_number;
                                DELETE FROM archive WHERE page_number=old.page_number;
                            END;

                            CREATE TRIGGER [on_complete]
                            AFTER INSERT ON archive
                            BEGIN DELETE FROM notebook WHERE page=new.page AND ix=new.ix AND what=new.what;
                            END;

                            INSERT INTO [table of contents](page_number, page)
                            VALUES(0, 'Main List');
                            """)
            #cursor.execute("commit")
            self.db = connection
            """self.preferences['Lists'] = {'Target List': 'Main List', 
                                         'Auto-Fetch': 'Next'}
            self.preferences['Date'] = {'Week Start': 'Sunday',
                                        'Date Format': 'MDY'}
            self.preferences['Time'] = {'24-Hour Time': False}"""

    def on_pre_start(self):
        global kv
        Builder.load_string(kv)
        del kv
    
    def build(self):
        ''''''
        self.dispatch('on_pre_start')
        app = Application()
        #inspector.create_inspector(Window, app)
        return app

    def on_start(self):
        app = self.root
        app.manager.transition = NoTransition()
        cursor = self.db.cursor()
        cursor.execute("""
                       SELECT page, page_number
                       FROM notebook
                       WHERE bookmark=1 and ix<3;
                       """)
        result = cursor.fetchall()

        if result:
            #assert(len(set(result)) == 1)
            page, page_number = result[0]

            if len(result) < 3:
                list_screen = app.manager.get_screen('List Screen')
                list_screen.page = page
                list_screen.page_number = page_number
                app.manager.current = 'List Screen'
            else:
                quickview_screen = app.manager.get_screen('QuickView Screen')
                quickview_screen.page = page
                quickview_screen.page_number = page_number
                app.manager.current = 'QuickView Screen'

        else:
            app.manager.current = 'Pages Screen'

    def on_pause(self):
        return True

    def on_stop(self):
        self.db.close()

if __name__ == '__main__':
    ThreeDoListApp().run()
