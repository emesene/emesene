# -*- coding: utf-8 -*-

from PyQt4  import QtGui
from PyQt4  import QtCore
from PyQt4.QtCore import Qt

import extension
import gui
from gui.qt4ui import Dialog
from gui.qt4ui import widgets

LIST = [
    {'stock_id' : 'preferences-desktop-accessibility','text' : ('Interface')},
    {'stock_id' : 'preferences-desktop-multimedia','text' : ('Sounds')},
    {'stock_id' : 'window-new','text' : ('Notifications')},
    {'stock_id' : 'preferences-desktop-theme','text' : ('Theme')},
    {'stock_id' : 'network-disconnect','text' : ('Extensions')},
    {'stock_id' : 'network-disconnect','text' : ('Plugins')},
]

class Preferences(QtGui.QWidget):
    NAME = 'Preferences'
    DESCRIPTION = 'A dialog to select the preferences'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, session, parent=None):
        """constructor
        """
        QtGui.QWidget.__init__(self, parent)
        
        self.setWindowTitle(("Preferences"))
        self.setWindowIcon(QtGui.QIcon(gui.theme.logo))
        self.resize(600, 400)
        
        self._session = session
        self.interface = Interface(session)
        self.sound = Sound(session)
        self.notification = Notification(session)
        self.theme = Theme(session)
        self.extension = Extension(session)
        #self.plugins = PluginWindow.PluginMainVBox(session)

        listView          = QListViewMod()
        self.widget_stack = QtGui.QStackedWidget()
        
        lay = QtGui.QHBoxLayout()
        lay.addWidget(listView)
        lay.addWidget(self.widget_stack)
        self.setLayout(lay)
        
        
        self._listModel = QtGui.QStandardItemModel(listView)
        seleModel = QtGui.QItemSelectionModel(self._listModel, listView)
        listView.setModel(self._listModel)
        listView.setSelectionModel(seleModel)
        self._delegate = listView.itemDelegate()
        
        listView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        listView.setIconSize(QtCore.QSize(32, 32))
        listView.setMovement(QtGui.QListView.Static)
        listView.setUniformItemSizes(True)
        listView.setResizeMode    (QtGui.QListView.Adjust)
        listView.setSizePolicy(QtGui.QSizePolicy.Fixed, 
                               QtGui.QSizePolicy.Expanding)
        for i in LIST:
            listItem = QtGui.QStandardItem(
                            QtGui.QIcon.fromTheme(i['stock_id']), i['text'])
            self._listModel.appendRow(listItem)
        
        for page in [self.interface,     self.sound, 
                     self.notification,  self.theme,
                     self.extension      ]: #self.plugins_page
            self.widget_stack.addWidget(page)
            
        
        listView.selectionModel().currentRowChanged.connect(
                                                        self._on_row_activated)



    def _on_row_activated(self,new_idx, old_idx):
        # Get information about the row that has been selected
        self.widget_stack.setCurrentIndex(new_idx.row())
        self.widget_stack.currentWidget().on_update()
        
    
    def _present(self):
        pass






class QListViewMod (QtGui.QListView):
    def __init__(self, parent=None):
        QtGui.QListView.__init__(self, parent)
        
    def sizeHint(self):
        width = 0
        height = 0
        rows = self.model().rowCount()
        option = QtGui.QStyleOptionViewItemV4()
        
        for i in range(rows):
            index = self.model().index(i, 0)
            size = self.itemDelegate().sizeHint(option, index)
            width = max(width, size.width())
            height = max(height, size.height())
        
        height = height * rows
        size = QtGui.QListView.sizeHint(self)
        return QtCore.QSize((2*width+size.width())/3, 
                            (2*height+size.height())/3)





class BaseTable(QtGui.QWidget):
    """a base table to display preferences
    """
    def __init__(self, rows, columns, homogeneous=False, parent=None):
        """constructor
        """
        QtGui.QWidget.__init__(self)
        
        # TODO: add checks for row and column values
        self._rows = rows
        self._columns = columns
        self._current_row = 0
        
        self.grid_lay = QtGui.QGridLayout()
        self.lay = QtGui.QVBoxLayout()
        self.lay.addLayout(self.grid_lay)
        self.lay.addStretch(2)
        self.setLayout(self.lay)
        
        self.grid_lay.setHorizontalSpacing(4)
        self.grid_lay.setVerticalSpacing(4)

        
    def attach(self, widget, column, col_span, row, row_span, *args):
        self.grid_lay.addWidget(widget, row, column, row_span, col_span)
        
    
    def append_row(self, widget, row=None):
        """append a row to the table
        """
        increment_current_row = False
        if row == None:
            row = self._current_row
            increment_current_row = True

        self.grid_lay.addWidget(widget, row, 0, 1, self._columns)

        if increment_current_row:
            self._current_row += 1
    
    
    def add_text(self, text, column, row, align_left=False, line_wrap=True):
        """add a label with thext to row and column, align the text left if
        align_left is True
        """
        label = QtGui.QLabel(text)
        self.add_label(label, column, row, align_left)


    def add_label(self, label, column, row, align_left=False, line_wrap=True):
        """add a label with thext to row and column, align the text left if
        align_left is True
        """
        if align_left:
            pass

        #label.set_line_wrap(line_wrap)
        self.grid_lay.addWidget(label, row, column)
    
    def append_markup(self, text):
        """append a label
        """
        label = QtGui.QLabel(text)
        self.append_row(label, None)
        

    def add_button(self, text, column, row, on_click):
        """add a button with text to the row and column, connect the clicked
        event to on_click"""
        button = QtGui.QPushButton(text)
        button.clicked.connect(on_click)
        self.grid_lay.addWidget(button, row, column)
        

    def append_entry_default(self, text, property_name, default):
        """append a row with a label and a line_edit, set the value to the
        value of property_name if exists, if not set it to default.
         Add a reset button that sets the value to the default"""

        def on_reset_clicked(button, entry, default):
            """called when the reset button is clicked, set
            entry text to default"""
            entry.setText(default)

        def on_entry_changed(entry, property_name):
            """called when the content of an entry changes,
            set the value of the property to the new value"""
            self.set_attr(property_name, entry.text())

        label = QtGui.QLabel(text)
        line_edit = QtGui.QLineEdit()
        reset = QtGui.QPushButton(QtGui.QIcon.fromTheme('edit-clear'), '')
        
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(label)
        hlay.addStretch()
        hlay.addWidget(line_edit)
        hlay.addWidget(reset)
        row = QtGui.QWidget()
        row.setLayout(hlay)
        self.append_row(row)
        
        text = self.get_attr(property_name)
        line_edit.setText(text)
        
        reset.clicked.connect(
                            lambda: on_reset_clicked(line_edit, default))
        line_edit.textChanged.connect(
                            lambda t: on_entry_changed(property_name))


    def append_check(self, text, property_name, row=None):
        """append a row with a check box with text as label and
        set the check state with default
        """
        # TODO: Inspect if we can put self.on_toggle inside this method.
        widget = QtGui.QCheckBox(text)
        
        self.append_row(widget, row)
        
        default = self.get_attr(property_name)
        widget.setChecked(default)
        
        widget.toggled.connect(lambda checked: self.on_toggled(widget, property_name))
        

    def append_range(self, text, property_name, min_val, max_val, is_int=True):
        """append a row with a scale to select an integer value between
        min and max
        """
        
        label = QtGui.QLabel(text)
        scale = QtGui.QSlider(Qt.Horizontal)
        
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(label)
        hlay.addWidget(scale)
        widget = QtGui.QWidget()
        widget.setLayout(hlay)
        self.append_row(widget, None)
        
        scale.setRange(min_val, max_val)
        default = self.get_attr(property_name)
        if default is None:
            default = min_val
        scale.setValue(default)

        #if is_int:
        #    scale.set_digits(0)
        
        scale.valueChanged.connect( lambda value: self.on_range_changed(
                                                            scale, 
                                                            property_name,
                                                            is_int))
        

    def append_combo(self, text, getter, property_name):
        """append a row with a check box with text as label and
        set the check state with default
        """
        label = QtGui.QLabel(text)
        combo = QtGui.QComboBox()
        
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(label)
        hlay.addWidget(combo)
        widget = QtGui.QWidget()
        widget.setLayout(hlay)
        self.append_row(widget, None)
        
        default = self.get_attr(property_name)
        count = 0
        default_count = 0
        for item in getter():
            combo.addItem(item)
            if item == default:
                default_count = count
            count += 1
        combo.setCurrentIndex(default_count)

        combo.currentIndexChanged.connect(
                    lambda text: self.on_combo_changed(combo, property_name))
        


    def on_combo_changed(self, combo, property_name):
        """callback called when the selection of the combo changed
        """
        self.set_attr(property_name, str(combo.currentText()))


    def on_range_changed(self, scale, property_name, is_int):
        """callback called when the selection of the combo changed
        """
        value = scale.value()
        if is_int:
            value = int(value)
        self.set_attr(property_name, value)
        

    def on_toggled(self, checkbutton, property_name):
        """default callback for a cehckbutton, set property_name
        to the status of the checkbutton
        """
        self.set_attr(property_name, checkbutton.isChecked())


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
        self.append_markup('<b>'+('Main window:')+'</b>')
        self.append_check(('Show user panel'),
            'session.config.b_show_userpanel')
        self.append_markup('<b>'+('Conversation window:')+'</b>')
        self.session.config.get_or_set('b_avatar_on_left', False)
        self.session.config.get_or_set('b_toolbar_small', False)
        self.append_check(('Start minimized/iconified'), 'session.config.b_conv_minimized')
        self.append_check(('Show emoticons'), 'session.config.b_show_emoticons')
        self.append_check(('Show conversation header'),
            'session.config.b_show_header')
        self.append_check(('Show conversation side panel'),
            'session.config.b_show_info')
        self.append_check(('Show conversation toolbar'),
            'session.config.b_show_toolbar')
        self.append_check(('Small conversation toolbar'),
            'session.config.b_toolbar_small')
        self.append_check(('Avatar on conversation left side'),
            'session.config.b_avatar_on_left')
        self.append_check(('Allow auto scroll in conversation'),
            'session.config.b_allow_auto_scroll')
        self.append_check(('Enable spell check if available (requires %s)') % 'python-gtkspell',
            'session.config.b_enable_spell_check')

        self.append_range(('Contact list avatar size'),
            'session.config.i_avatar_size', 18, 64)
        self.append_range(('Conversation avatar size'),
            'session.config.i_conv_avatar_size', 18, 128)





class Sound(BaseTable):
    """the panel to display/modify the config related to the sounds
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 6, 1)
        self.session = session
        self.append_markup('<b>'+('Messages events:')+'</b>')
        self.append_check(('Mute sounds'),
            'session.config.b_mute_sounds')
        self.append_check(('Play sound on sent message'),
            'session.config.b_play_send')
        self.append_check(('Play sound on first received message'),
            'session.config.b_play_first_send')
        self.append_check(('Play sound on received message'),
            'session.config.b_play_type')
        self.append_check(('Play sound on nudge'),
            'session.config.b_play_nudge')

        self.append_markup('<b>'+('Users events:')+'</b>')
        self.append_check(('Play sound on contact online'),
            'session.config.b_play_contact_online')
        self.append_check(('Play sound on contact offline'),
            'session.config.b_play_contact_offline')





class Notification(BaseTable):
    """the panel to display/modify the config related to the notifications
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 2, 1)
        self.session = session
        self.append_check(('Notify on contact online'),
            'session.config.b_notify_contact_online')
        self.append_check(('Notify on contact offline'),
            'session.config.b_notify_contact_offline')
        self.append_check(('Notify on received message'),
            'session.config.b_notify_receive_message')





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

        self.append_combo(('Image theme'), gui.theme.get_image_themes,
            'session.config.image_theme')
        self.append_combo(('Sound theme'), gui.theme.get_sound_themes,
            'session.config.sound_theme')
        self.append_combo(('Emote theme'), gui.theme.get_emote_themes,
            'session.config.emote_theme')
        self.append_combo(('Adium theme'), gui.theme.get_adium_themes,
            'session.config.adium_theme')
        self.append_entry_default(('Nick format'),
                'session.config.nick_template', ContactList.NICK_TPL)
        self.append_entry_default(('Group format'),
                'session.config.group_template', ContactList.GROUP_TPL)





class Extension(BaseTable):
    """the panel to display/modify the config related to the extensions_cmb
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 8, 2)
        self._session = session

        self.category_info    = QtGui.QLabel('')
        self.name_info        = QtGui.QLabel('')
        self.description_info = QtGui.QLabel('')
        self.author_info      = QtGui.QLabel('')
        self.website_info     = QtGui.QLabel('')
        self.extensions_cmb   = QtGui.QComboBox()
        self.categories_cmb   = QtGui.QComboBox()
        self.extension_list   = []

        self._setup_ui()
        

    def _setup_ui(self):
        """add the widgets that will display the information of the 
        extension category and the selected extension and widgets 
        to display the extensions"""
        
        self.add_text(('Categories'),  0, 0, True)
        self.add_text(('Selected'),    0, 1, True)
        self.add_text('',              0, 2, True)
        self.add_text(('Name'),        0, 3, True)
        self.add_text(('Description'), 0, 4, True)
        self.add_text(('Author'),      0, 5, True)
        self.add_text(('Website'),     0, 6, True)
        self.add_label(self.name_info,        1, 3, True)
        self.add_label(self.description_info, 1, 4, True)
        self.add_label(self.author_info,      1, 5, True)
        self.add_label(self.website_info,     1, 6, True)
        self.add_button(_('Redraw main screen'), 1, 7,
                self._on_redraw_main_screen)
        self.attach(self.categories_cmb, 1, 2, 0, 1)
        self.attach(self.extensions_cmb, 1, 2, 1, 2)
        
        categories = self._get_categories()
        for item in categories:
            print 'category item: %s' % item
            self.categories_cmb.addItem(item)
        self.categories_cmb.setCurrentIndex(0)
        self._on_category_changed(self.categories_cmb)
        
        self.categories_cmb.currentIndexChanged.connect(lambda text: self._on_category_changed(self.categories_cmb))
        self.extensions_cmb.currentIndexChanged.connect(lambda text: self._on_extension_changed(self.extensions_cmb))
        
        
    def _on_redraw_main_screen(self, button):
        """called when the Redraw main screen button is clicked"""
        self._session.save_config()
        self._session.signals.login_succeed.emit()
        self._session.signals.contact_list_ready.emit()


    def _on_category_changed(self, combo):
        """callback called when the category on the combo changes"""
        self.extensions_cmb.model().clear()
        self.extension_list = []
        category = str(combo.currentText())
        default = extension.get_default(category)
        extensions = extension.get_extensions(category)
        
        count = 0
        selected = 0
        for identifier, ext in extensions.iteritems():
            if default is ext:
                selected = count

            self.extension_list.append((ext, identifier))
            self.extensions_cmb.addItem(self.get_attr_or_default(ext, 'NAME',
                ext.__name__))
            count += 1

        self.extensions_cmb.setCurrentIndex(selected)
        self._on_extension_changed(self.extensions_cmb)
        

    def _on_extension_changed(self, combo):
        """callback called when the extension on the combo changes"""
        category = str(self.categories_cmb.currentText())
        extension_index = self.extensions_cmb.currentIndex()

        # when the model is cleared this event is emited
        if extension_index == -1:
            return
        
        ext, identifier = self.extension_list[extension_index]
        if not extension.set_default_by_id(category, identifier):
            # TODO: revert the selection to the previous selected extension
            log.warning(_('Could not set %s as default extension for %s') % \
                (extension_id, category))
            return

        ext = extension.get_default(category)
        self._set_extension_info(ext)
    

    def on_update(self):
        '''called when changed to this page'''
        # empty categories combo
        model = self.categories_cmb.model().clear()
        # fill it again with available categories
        # this is done because a plugin may have changed them
        categories = self._get_categories()
        for item in categories:
            self.categories_cmb.addItems([item])
        self.categories_cmb.setCurrentIndex(0)

    
    def _set_extension_info(self, ext):
        """fill the information about the ext"""
        name        = self.get_attr_or_default(ext, 'NAME', '?')
        description = self.get_attr_or_default(ext, 'DESCRIPTION', '?')
        author      = self.get_attr_or_default(ext, 'AUTHOR', '?')
        website     = self.get_attr_or_default(ext, 'WEBSITE', '?')

        self.name_info.setText(name)
        self.description_info.setText(description)
        self.author_info.setText(author)
        self.website_info.setText(website)
        

    def _get_categories(self):
        ''' get available categories'''
        categories = [ctg for ctg in extension.get_categories().keys() if len(extension.get_extensions(ctg)) > 1]
        categories.sort()
        return categories
