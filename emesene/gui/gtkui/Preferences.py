import gtk

import gui
import utils
import extension

import PluginWindow

import logging
log = logging.getLogger('gtkui.Preferences')

LIST = [
    {'stock_id' : gtk.STOCK_FULLSCREEN,'text' : _('Interface')},
    {'stock_id' : gtk.STOCK_MEDIA_NEXT,'text' : _('Sounds')},
    {'stock_id' : gtk.STOCK_LEAVE_FULLSCREEN,'text' : _('Notifications')},
    {'stock_id' : gtk.STOCK_SELECT_COLOR,'text' : _('Theme')},
    {'stock_id' : gtk.STOCK_DISCONNECT,'text' : _('Extensions')},
    {'stock_id' : gtk.STOCK_DISCONNECT,'text' : _('Plugins')},
]

class Preferences(gtk.Window):
    """A window to display/modify the preferences
    """

    def __init__(self, session):
        """constructor
        """
        gtk.Window.__init__(self)
        self.set_border_width(2)
        self.set_title("Preferences")
        self.session = session

        self.set_default_size(600, 400)
        self.set_role("New preferences Window")
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)

        if utils.file_readable(gui.theme.logo):
            self.set_icon(
                utils.safe_gtk_image_load(gui.theme.logo).get_pixbuf())

        ''' TREE VIEW STUFF '''
        # Create the list store model for the treeview.
        listStore = gtk.ListStore(gtk.gdk.Pixbuf, str)

        for i in LIST:
            # we should use always the same icon size,
            # we can remove that field in LIST
            listStore.append([self.render_icon(i['stock_id'],
                             gtk.ICON_SIZE_LARGE_TOOLBAR), i['text']])

        # Create the TreeView
        treeView = gtk.TreeView(listStore)

        # Create the renders
        cellText = gtk.CellRendererText()
        cellPix = gtk.CellRendererPixbuf()

        # Create the single Tree Column
        treeViewColumn = gtk.TreeViewColumn('Categories')

        treeViewColumn.pack_start(cellPix, expand=False)
        treeViewColumn.add_attribute(cellPix, 'pixbuf',0)
        treeViewColumn.pack_start(cellText, expand=True)
        treeViewColumn.set_attributes(cellText, text=1)

        treeView.append_column(treeViewColumn)
        treeView.set_headers_visible(False)
        treeView.connect('cursor-changed', self._on_row_activated)
        self.treeview = treeView

        self.notebook = gtk.Notebook()
        self.notebook.set_show_tabs(False)
        self.notebook.set_resize_mode(gtk.RESIZE_QUEUE)
        self.notebook.set_scrollable(True)

        ''' PACK TREEVIEW, FRAME AND HBOX '''
        vbox = gtk.VBox()

        vbox.set_spacing(4)
        hbox = gtk.HBox(homogeneous=False, spacing=5)
        hbox.pack_start(treeView, True,True) # False, True
        hbox.pack_start(self.notebook, True, True)
        vbox.pack_start(hbox, True,True) # hbox, True, True

        self.interface = Interface(session)
        self.sound = Sound(session)
        self.notification = Notification(session)
        self.theme = Theme(session)
        self.extension = Extension(session)
        self.plugins = PluginWindow.PluginMainVBox(session)

        self.buttons = gtk.HButtonBox()
        self.buttons.set_border_width(2)
        self.buttons.set_layout(gtk.BUTTONBOX_END)
        self.close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.close.connect('clicked', lambda *args: self.hide())
        self.buttons.pack_start(self.close)

        # Create a dict that stores each page
        self.page_dict = []

        # Keep local copies of the objects
        self.interface_page = self.interface
        self.sound_page = self.sound
        self.notifications_page = self.notification
        self.theme_page = self.theme
        self.extensions_page = self.extension
        self.plugins_page = self.plugins

        # Whack the pages into a dict for future reference

        self.page_dict.append(self.interface_page)
        self.page_dict.append(self.sound_page)
        self.page_dict.append(self.notifications_page)
        self.page_dict.append(self.theme_page)
        self.page_dict.append(self.extensions_page)
        self.page_dict.append(self.plugins_page)

        for i in range(len(self.page_dict)):
           self.notebook.append_page(self.page_dict[i])

        self.add(vbox)
        vbox.show_all()

    def _on_row_activated(self,treeview):
        # Get information about the row that has been selected
        cursor, obj = treeview.get_cursor()
        self.showPage(cursor[0])

    def showPage(self, index):
        self.notebook.set_current_page(index)
        self.current_page = index
        self.page_dict[index].on_update()

class BaseTable(gtk.Table):
    """a base table to display preferences
    """
    def __init__(self, rows, columns, homogeneous=False):
        """constructor
        """
        gtk.Table.__init__(self, rows, columns, homogeneous)
        self.rows = rows
        self.columns = columns
        self.set_row_spacings(4)
        self.set_col_spacings(4)

        self.current_row = 0

    def add_text(self, text, column, row, align_left=False, line_wrap=True):
        """add a label with thext to row and column, align the text left if
        align_left is True
        """
        label = gtk.Label(text)
        self.add_label(label, column, row, align_left)

    def add_label(self, label, column, row, align_left=False, line_wrap=True):
        """add a label with thext to row and column, align the text left if
        align_left is True
        """
        if align_left:
            label.set_alignment(0.0, 0.5)

        label.set_line_wrap(line_wrap)
        self.attach(label, column, column + 1, row, row + 1)

    def add_button(self, text, column, row, on_click, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL):
        """add a button with text to the row and column, connect the clicked
        event to on_click"""
        button = gtk.Button(text)
        button.connect('clicked', on_click)
        self.attach(button, column, column + 1, row, row + 1, xoptions,
                yoptions)

    def append_row(self, widget, row=None):
        """append a row to the table
        """
        increment_current_row = False
        if row == None:
            row = self.current_row
            increment_current_row = True

        self.attach(widget, 0, self.columns, row, row + 1, yoptions=gtk.SHRINK)

        if increment_current_row:
            self.current_row += 1

    def append_entry_default(self, text, property_name, default):
        """append a row with a label and a entry, set the value to the
        value of property_name if exists, if not set it to default.
         Add a reset button that sets the value to the default"""

        def on_reset_clicked(button, entry, default):
            """called when the reset button is clicked, set
            entry text to default"""
            entry.set_text(default)

        def on_entry_changed(entry, property_name):
            """called when the content of an entry changes,
            set the value of the property to the new value"""
            self.set_attr(property_name, entry.get_text())

        hbox = gtk.HBox(spacing=4)
        hbox.set_homogeneous(True)
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        text = self.get_attr(property_name)

        entry = gtk.Entry()
        entry.set_text(text)

        reset = gtk.Button(stock=gtk.STOCK_CLEAR)

        hbox.pack_start(label, True, True)
        hbox.pack_start(entry, False)
        hbox.pack_start(reset, False)

        reset.connect('clicked', on_reset_clicked, entry, default)
        entry.connect('changed', on_entry_changed, property_name)
        self.append_row(hbox, None)

    def append_check(self, text, property_name, row=None):
        """append a row with a check box with text as label and
        set the check state with default
        """
        default = self.get_attr(property_name)
        widget = gtk.CheckButton(text)
        widget.set_active(default)
        widget.connect('toggled', self.on_toggled, property_name)
        self.append_row(widget, row)

    def append_range(self, text, property_name, min_val, max_val, is_int=True):
        """append a row with a scale to select an integer value between
        min and max
        """
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        default = self.get_attr(property_name)

        if default is None:
            default = min_val

        scale = gtk.HScale()
        scale.set_range(min_val, max_val)
        scale.set_value(default)

        if is_int:
            scale.set_digits(0)

        hbox.pack_start(label, True, True)
        hbox.pack_start(scale, False)

        scale.connect('value-changed', self.on_range_changed, property_name,
                is_int)
        self.append_row(hbox, None)

    def append_combo(self, text, getter, property_name):
        """append a row with a check box with text as label and
        set the check state with default
        """
        default = self.get_attr(property_name)
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        combo = gtk.combo_box_new_text()

        count = 0
        default_count = 0
        for item in getter():
            combo.append_text(item)
            if item == default:
                default_count = count

            count += 1

        combo.set_active(default_count)

        hbox.pack_start(label, True, True)
        hbox.pack_start(combo, False)

        combo.connect('changed', self.on_combo_changed, property_name)
        self.append_row(hbox, None)

    def append_markup(self, text):
        """append a label
        """
        hbox = gtk.HBox()
        hbox.set_homogeneous(True)
        label = gtk.Label()
        label.set_alignment(0.0, 0.5)
        label.set_markup(text)

        hbox.pack_start(label, True, True)

        self.append_row(hbox, None)

    def on_combo_changed(self, combo, property_name):
        """callback called when the selection of the combo changed
        """
        self.set_attr(property_name, combo.get_active_text())

    def on_range_changed(self, scale, property_name, is_int):
        """callback called when the selection of the combo changed
        """
        value = scale.get_value()

        if is_int:
            value = int(value)

        self.set_attr(property_name, value)

    def on_toggled(self, checkbutton, property_name):
        """default callback for a cehckbutton, set property_name
        to the status of the checkbutton
        """
        self.set_attr(property_name, checkbutton.get_active())

    def get_attr(self, name):
        """return the value of an attribute, if it has dots, then
        get the values until the last
        """

        obj = self
        for attr in name.split('.'):
            obj = getattr(obj, attr)

        return obj

    def set_attr(self, name, value):
        """set the value of an attribute, if it has dots, then
        get the values until the last
        """

        obj = self
        terms = name.split('.')

        for attr in terms[:-1]:
            obj = getattr(obj, attr)

        setattr(obj, terms[-1], value)
        return obj

    def get_attr_or_default(self, obj, name, default=None):
        """try to get the value of the attribute 'name' from obj, if it
        doesn't exist return default"""
        if not hasattr(obj, name):
            return default

        return getattr(obj, name)

    def on_update(self):
        pass

class Interface(BaseTable):
    """the panel to display/modify the config related to the gui
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 4, 1)
        self.session = session
        self.append_markup('<b>Main window:</b>')
        self.append_check('Show user panel',
            'session.config.b_show_userpanel')
        self.append_markup('<b>Conversation window:</b>')
        self.session.config.get_or_set('b_avatar_on_left', False)
        self.append_check('Show emoticons', 'session.config.b_show_emoticons')
        self.append_check('Show conversation header',
            'session.config.b_show_header')
        self.append_check('Show conversation side panel',
            'session.config.b_show_info')
        self.append_check('Show conversation toolbar',
            'session.config.b_show_toolbar')
        self.append_check('Avatar on conversation left side',
            'session.config.b_avatar_on_left')
        self.append_check('Allow auto scroll in conversation',
            'session.config.b_allow_auto_scroll')

        self.append_range('Contact list avatar size',
            'session.config.i_avatar_size', 18, 64)
        self.append_range('Conversation avatar size',
            'session.config.i_conv_avatar_size', 18, 128)
        self.show_all()

class Sound(BaseTable):
    """the panel to display/modify the config related to the sounds
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 6, 1)
        self.session = session
        self.append_markup('<b>Messages events:</b>')
        self.append_check('Play sound on first sent message',
            'session.config.b_play_first_send')
        self.append_check('Play sound on sent message',
            'session.config.b_play_send')
        self.append_check('Play sound on received message',
            'session.config.b_play_type')
        self.append_check('Play sound on nudge',
            'session.config.b_play_nudge')

        self.append_markup('<b>Users events:</b>')
        self.append_check('Play sound on contact online',
            'session.config.b_play_contact_online')
        self.append_check('Play sound on contact offline',
            'session.config.b_play_contact_offline')
        self.show_all()

class Notification(BaseTable):
    """the panel to display/modify the config related to the notifications
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 2, 1)
        self.session = session
        self.append_check('Notify on contact online',
            'session.config.b_notify_contact_online')
        self.append_check('Notify on contact offline',
            'session.config.b_notify_contact_offline')
        self.append_check('Notify on received message',
            'session.config.b_notify_receive_message')
        self.show_all()

class Theme(BaseTable):
    """the panel to display/modify the config related to the theme
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 5, 1)
        self.session = session

        ContactList = extension.get_default('contact list')

        adium_theme = self.session.config.get_or_set('adium_theme', 'renkoo')

        self.append_combo('Image theme', gui.theme.get_image_themes,
            'session.config.image_theme')
        self.append_combo('Sound theme', gui.theme.get_sound_themes,
            'session.config.sound_theme')
        self.append_combo('Emote theme', gui.theme.get_emote_themes,
            'session.config.emote_theme')
        self.append_combo('Adium theme', gui.theme.get_adium_themes,
            'session.config.adium_theme')
        self.append_entry_default('Nick format',
                'session.config.nick_template', ContactList.NICK_TPL)
        self.append_entry_default('Group format',
                'session.config.group_template', ContactList.GROUP_TPL)

class Extension(BaseTable):
    """the panel to display/modify the config related to the extensions
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 8, 2)
        self.session = session

        self.category_info = gtk.Label('')
        self.name_info = gtk.Label('')
        self.description_info = gtk.Label('')
        self.author_info = gtk.Label('')
        self.website_info = gtk.Label('')
        self.extensions = gtk.combo_box_new_text()
        self.categories = gtk.combo_box_new_text()
        self.extension_list = []

        self._add_info_widgets()
        self._add_categories_and_extensions_combos()

    def _add_info_widgets(self):
        """add the widgets that will display the information of the extension
        category and the selected extension
        """
        self.add_text('Categories', 0, 0, True)
        self.add_text('Selected', 0, 1, True)
        self.add_text('', 0, 2, True)
        self.add_text('Name', 0, 3, True)
        self.add_text('Description', 0, 4, True)
        self.add_text('Author', 0, 5, True)
        self.add_text('Website', 0, 6, True)

        self.add_label(self.name_info, 1, 3, True)
        self.add_label(self.description_info, 1, 4, True)
        self.add_label(self.author_info, 1, 5, True)
        self.add_label(self.website_info, 1, 6, True)

        self.add_button('Redraw main screen', 1, 7,
                self._on_redraw_main_screen, 0, 0)

    def _on_redraw_main_screen(self, button):
        """called when the Redraw main screen button is clicked"""
        self.session.save_config()
        self.session.signals.login_succeed.emit()
        self.session.signals.contact_list_ready.emit()

    def _get_categories(self):
        ''' get available categories'''
        categories = [ctg for ctg in extension.get_categories().keys() if len(extension.get_extensions(ctg)) > 1]
        categories.sort()
        return categories

    def _add_categories_and_extensions_combos(self):
        """add the widgets to display the extensions"""

        categories = self._get_categories()

        for item in categories:
            self.categories.append_text(item)

        self.categories.connect('changed', self._on_category_changed)
        self.extensions.connect('changed', self._on_extension_changed)
        self.attach(self.categories, 1, 2, 0, 1, yoptions=gtk.EXPAND)
        self.attach(self.extensions, 1, 2, 1, 2, yoptions=gtk.EXPAND)
        self.categories.set_active(0)

    def _on_category_changed(self, combo):
        """callback called when the category on the combo changes"""
        self.extensions.get_model().clear()
        self.extension_list = []
        category = combo.get_active_text()
        default = extension.get_default(category)
        extensions = extension.get_extensions(category)

        count = 0
        selected = 0
        for identifier, ext in extensions.iteritems():
            if default is ext:
                selected = count

            self.extensions.append_text(self.get_attr_or_default(ext, 'NAME',
                ext.__name__))
            self.extension_list.append((ext, identifier))
            count += 1

        self.extensions.set_active(selected)

    def _on_extension_changed(self, combo):
        """callback called when the extension on the combo changes"""
        category = self.categories.get_active_text()
        extension_index = self.extensions.get_active()

        # when the model is cleared this event is emited
        if extension_index == -1:
            return

        ext, identifier = self.extension_list[extension_index]
        if not extension.set_default_by_id(category, identifier):
            # TODO: revert the selection to the previous selected extension
            log.warning('Could not set %s as default extension for %s' % \
                (extension_id, category))
            return

        ext = extension.get_default(category)
        self._set_extension_info(ext)

    def _set_extension_info(self, ext):
        """fill the information about the ext"""
        name = self.get_attr_or_default(ext, 'NAME', '?')
        description = self.get_attr_or_default(ext, 'DESCRIPTION', '?')
        author = self.get_attr_or_default(ext, 'AUTHOR', '?')
        website = self.get_attr_or_default(ext, 'WEBSITE', '?')

        self.name_info.set_text(name)
        self.description_info.set_text(description)
        self.author_info.set_text(author)
        self.website_info.set_text(website)

    def on_update(self):
        '''called when changed to this page'''
        # empty categories combo
        model = self.categories.get_model()
        self.categories.set_model(None)
        model.clear()
        # fill it again with available categories
        # this is done because a plugin may have changed them
        categories = self._get_categories()
        for item in categories:
            model.append([item])
        self.categories.set_model(model)
        self.categories.set_active(0)




