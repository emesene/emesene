import gtk

import gui
import utils

class Preferences(gtk.Window):
    """
    A window to display/modify the preferences
    """

    def __init__(self, session):
        """
        constructor
        """
        gtk.Window.__init__(self)
        self.set_title("Preferences")

        self.set_default_size(320, 260)
        self.set_role("preferences")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        if utils.file_readable(gui.theme.logo):
            self.set_icon(
                utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())

        self.box = gtk.VBox()
        self.tabs = gtk.Notebook()

        self.interface = Interface(session)
        self.sound = Sound(session)
        self.notification = Notification(session)

        self.buttons = gtk.HButtonBox()
        self.buttons.set_layout(gtk.BUTTONBOX_END)
        self.close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.close.connect('clicked', lambda *args: self.hide())
        self.buttons.pack_start(self.close)

        self.tabs.append_page(self.interface, gtk.Label('Interface'))
        self.tabs.append_page(self.sound, gtk.Label('Sounds'))
        self.tabs.append_page(self.notification, gtk.Label('Notifications'))

        self.box.pack_start(self.tabs, True, True)
        self.box.pack_start(self.buttons, False)

        self.add(self.box)
        self.box.show_all()

class BaseTable(gtk.Table):
    """
    a base table to display preferences
    """
    def __init__(self, rows, columns, homogeneous=False):
        """
        constructor
        """
        gtk.Table.__init__(self, rows, columns, homogeneous)
        self.rows = rows
        self.columns = columns

        self.current_row = 0

    def append_row(self, widget, row=None):
        """
        append a row to the table
        """
        increment_current_row = False
        if row == None:
            row = self.current_row
            increment_current_row = True

        self.attach(widget, 0, self.columns, row, row + 1)

        if increment_current_row:
            self.current_row += 1

    def append_check(self, text, property_name, row=None):
        """
        append a row with a check box with text as label and
        set the check state with default
        """
        default = self.get_attr(property_name)
        widget = gtk.CheckButton(text)
        widget.set_active(default)
        widget.connect('toggled', self.on_toggled, property_name)
        self.append_row(widget, row)

    def on_toggled(self, checkbutton, property_name):
        """
        default callback for a cehckbutton, set property_name
        to the status of the checkbutton
        """
        self.set_attr(property_name, checkbutton.get_active())

    def get_attr(self, name):
        """
        return the value of an attribute, if it has dots, then
        get the values until the last
        """

        obj = self
        for attr in name.split('.'):
            obj = getattr(obj, attr)

        return obj

    def set_attr(self, name, value):
        """
        set the value of an attribute, if it has dots, then
        get the values until the last
        """

        obj = self
        terms = name.split('.')

        for attr in terms[:-1]:
            obj = getattr(obj, attr)

        setattr(obj, terms[-1], value)
        return obj

class Interface(BaseTable):
    """
    the panel to display/modify the config related to the gui
    """

    def __init__(self, session):
        """
        constructor
        """
        BaseTable.__init__(self, 4, 1)
        self.session = session
        self.append_check('Show emoticons', 'session.config.b_show_emoticons')
        self.append_check('Show conversation header', 
            'session.config.b_show_header')
        self.append_check('Show conversation side panel', 
            'session.config.b_show_info')
        self.append_check('Show conversation toolbar', 
            'session.config.b_show_toolbar')
        self.append_check('Show user panel', 
            'session.config.b_show_userpanel')
        self.show_all()

class Sound(BaseTable):
    """
    the panel to display/modify the config related to the sounds
    """

    def __init__(self, session):
        """
        constructor
        """
        BaseTable.__init__(self, 6, 1)
        self.session = session
        self.append_check('Play sound on first sent message', 
            'session.config.b_play_first_send')
        self.append_check('Play sound on sent message', 
            'session.config.b_play_send')
        self.append_check('Play sound on received message', 
            'session.config.b_play_type')
        self.append_check('Play sound on nudge', 
            'session.config.b_play_nudge')
        self.append_check('Play sound on contact online', 
            'session.config.b_play_contact_online')
        self.append_check('Play sound on contact offline', 
            'session.config.b_play_contact_offline')
        self.show_all()

class Notification(BaseTable):
    """
    the panel to display/modify the config related to the notifications
    """

    def __init__(self, session):
        """
        constructor
        """
        BaseTable.__init__(self, 2, 1)
        self.session = session
        self.append_check('Notify on contact online', 
            'session.config.b_notify_contact_online')
        self.append_check('Notify on contact offline', 
            'session.config.b_notify_contact_offline')
        self.show_all()

