import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import NoTransition
from kivy.properties import ListProperty, ObjectProperty
from apsw import Connection, SQLITE_OPEN_READWRITE, CantOpenError

kv = """
#:import ListScreen listscreen.ListScreen
#:import PagesScreen pagesscreen.PagesScreen
#:import ArchiveScreen archivescreen.ArchiveScreen
#:import QuickViewScreen quickviewscreen.QuickViewScreen
##:import DateTimeMiniScreen datepickerminiscreen.DateTimeMiniScreen
#:import ScreenManager kivy.uix.screenmanager.ScreenManager

<Application>:
    manager: manager_id

    ScreenManager:
        id: manager_id
        size: root.size
        pos: root.pos
        canvas.before:
            Color:
                rgba: app.smoke_white
            Rectangle:
                size: self.size
                pos: self.pos

        PagesScreen:
            root_directory: app.db
        QuickViewScreen:
            root_directory: app.db
        ListScreen:
            root_directory: app.db
        ArchiveScreen:
            root_directory: app.db
        #DateTimeMiniScreen:
            #root_directory: app.db
"""

class Application(Widget):
    manager = ObjectProperty(None)

class ThreeDoListApp(App):
    """Special Thanks to Joe Jimenez of Breezi[dot]com for breezi_font-webfont.ttf""" 
    ### Colors ###
    no_color = ListProperty((0.0, 0.0, 0.0, 0.0))
    light_blue = ListProperty((0.498, 0.941, 1.0, 1.0))
    blue = ListProperty((0.0, 0.824, 1.0, 1.0))
    red = ListProperty((1.0, 0.549, 0.5294, 1.0))
    dark_blue = ListProperty((0.0784, 0.349, 0.604, 1.0))
    purple = ListProperty((0.451, 0.4627, 0.561, 1.0))
    white = ListProperty((1.0, 1.0, 1.0, 1.0))
    light_gray = ListProperty((1.0, 0.98, 0.941, 1.0))
    smoke_white = ListProperty((0.95, 0.97, 0.973, 1.0))
    gray = ListProperty((0.9137, 0.933, 0.9451, 1.0))
    dark_gray = ListProperty((0.533, 0.533, 0.533, 1.0))
    shadow_gray = ListProperty((0.8, 0.8, 0.8, 1.0))
    black = ListProperty((0.0, 0.0, 0.0, 1.0))
    
    try:
        db = ObjectProperty(Connection(os.path.expanduser('~/Documents/threedolist/db.db'), flags=SQLITE_OPEN_READWRITE))
    except CantOpenError:
        db = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.register_event_type('on_pre_start')
        super(ThreeDoListApp, self).__init__(**kwargs)

        if not self.db:
            connection = Connection(self.user_data_dir + '/db.db')
            cursor = connection.cursor()
            cursor.execute("""
                           PRAGMA user_version=1;

                           CREATE TABLE [table of contents](
                           page_number UNSIGNED INTEGER,
                           page TEXT PRIMARY KEY,
                           bookmark UNSIGNED SHORT INTEGER DEFAULT 0;

                           CREATE TABLE [notebook](
                           ix UNSIGNED INTEGER,
                           what TEXT DEFAULT '',
                           when_ TEXT DEFAULT '',
                           where_ TEXT DEFAULT '',
                           why UNSIGNED SHORT INTEGER DEFAULT 0,
                           how TEXT DEFAULT '',
                           page TEXT,
                           UNIQUE(page, ix),
                           FOREIGN KEY(page) REFERENCES [table of contents](page) ON DELETE CASCADE ON UPDATE CASCADE);

                           CREATE TABLE [archive](
                           ix UNSIGNED INTEGER,
                           what TEXT DEFAULT '',
                           when_ TEXT DEFAULT '',
                           where_ TEXT DEFAULT '',
                           why UNSIGNED SHORT INTEGER DEFAULT 0,
                           how TEXT DEFAULT '',
                           page TEXT,
                           FOREIGN KEY(page) REFERENCES [table of contents](page) ON DELETE CASCADE ON UPDATE CASCADE);

                           CREATE TRIGGER [on_new_page]
                           AFTER INSERT ON [table of contents]
                           BEGIN
                               INSERT INTO [notebook](page, ix) VALUES(NEW.page, 1);
                               INSERT INTO [notebook](page, ix) VALUES(NEW.page, 2);
                               INSERT INTO [notebook](page, ix) VALUES(NEW.page, 3);
                           END;

                           CREATE TRIGGER [soft_delete]
                           BEFORE DELETE ON [notebook]
                           WHEN OLD.ix<4 AND OLD.page=(SELECT page FROM [table of contents] WHERE bookmark=1)
                           BEGIN
                               UPDATE [notebook] SET what='', when_='', where_='', why=0, how='' WHERE ix=OLD.ix AND page=OLD.page;
                               SELECT RAISE(IGNORE);
                           END;

                           CREATE TRIGGER [new_action_item]
                           AFTER UPDATE ON [notebook]
                           WHEN NEW.what=''
                           BEGIN
                               DELETE FROM [notebook] WHERE ix>3 AND WHAT='' AND page=(SELECT page FROM [table of contents] WHERE bookmark=1);
                           END;

                           CREATE TRIGGER [on_complete]
                           AFTER INSERT ON archive
                           BEGIN
                               DELETE FROM [notebook] WHERE page=NEW.page AND ix=NEW.ix AND what=NEW.what;
                           END;

                           INSERT INTO [table of contents](page_number, page)
                           VALUES(1, 'Main List');

                           INSERT INTO [table of contents](page_number, page) VALUES(2, 'Sample List');
                           UPDATE [notebook] SET what='Click Me', when_='', where_='', why=0, how='Double-tap any one of us' WHERE page='Sample List' AND ix=1;
                           INSERT INTO [notebook](page, ix, what, how) VALUES('Sample List', 4, 'Swipe right to complete me', 'You can find me later in the "Archive Screen"');
                           INSERT INTO [notebook](page, ix, what, how) VALUES('Sample List', 5, 'Swipe left to delete me', 'You can also delete a list itself in the "List Screen" this way.');
                           INSERT INTO [notebook](page, ix, what, how) VALUES('Sample List', 6, 'Double-tap to rename me', 'You can also rename a list itself in the "List Screen" this way.');
                           INSERT INTO [notebook](page, ix, what, how) VALUES('Sample List', 7, 'Press and hold to Drag-N''-Drop', 'You can re-order your tasks this way.');
                           INSERT INTO [notebook](page, ix, what, how) VALUES('Sample List', 8, 'Drag me to an "Action Item".', 'The "Action Items" are your top 3 tasks to focus on at a time.');
                           """)
            self.db = connection
            
        self.db.cursor().execute("PRAGMA foreign_keys=ON;")

    def on_pre_start(self):
        global kv
        Builder.load_string(kv)
        del kv
    
    def build(self):
        ''''''
        self.dispatch('on_pre_start')
        app = Application()
        return app

    def on_start(self):
        app = self.root
        app.manager.transition = NoTransition()
        cursor = self.db.cursor()
        cursor.execute("""
                       SELECT DISTINCT note.page, contents.page_number, (SELECT COUNT(*) FROM [notebook] WHERE ix<4 AND what<>'' AND page=note.page)
                       FROM [table of contents] AS contents, [notebook] AS note
                       WHERE contents.page=note.page
                       AND contents.bookmark=1;
                       """)
        result = cursor.fetchall()

        if result:
            page, page_number, l = result[0]

            if l < 3:
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
