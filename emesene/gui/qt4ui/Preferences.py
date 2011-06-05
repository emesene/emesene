# -*- coding: utf-8 -*-

'''This module contains classes used to build up a Preferences window'''

import logging
import webbrowser

from PyQt4  import QtGui
from PyQt4  import QtCore
from PyQt4.QtCore import Qt

from gui.qt4ui.Utils import tr

import e3.common
import extension
import gui


log = logging.getLogger('qt4ui.Preferences')

LIST = [
    {'stock_id' : 'preferences-desktop-accessibility', 'text' : tr('Interface')},
    {'stock_id' : 'preferences-desktop',               'text' : tr('Desktop'  )},
    {'stock_id' : 'preferences-desktop-multimedia',    'text' : tr('Sounds'   )},
    {'stock_id' : 'window-new',                    'text' : tr('Notifications')},
    {'stock_id' : 'preferences-desktop-theme',         'text' : tr('Theme'    )},
    {'stock_id' : 'network-disconnect',            'text' : tr('Extensions'   )},
    {'stock_id' : 'network-disconnect',                'text' : tr('Plugins'  )},
]

class Preferences(QtGui.QWidget):
    '''This class represents the Preferences window'''
    NAME = 'Preferences'
    DESCRIPTION = 'A dialog to select the preferences'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    def __init__(self, session, parent=None):
        '''constructor'''
        QtGui.QWidget.__init__(self, parent)
        
        self.setWindowTitle(tr('Preferences'))
        self.setWindowIcon(QtGui.QIcon(gui.theme.get_image_theme().logo))
        self.resize(600, 400)
        
        self._session = session
        #TODO: check
        self.session = session
        self.interface    = Interface(session)
        self.desktop      = Desktop(session)
        self.sound        = Sound(session)
        self.notification = Notification(session)
        self.theme        = Theme(session)
        self.extension    = Extension(session)
        #self.plugins     = PluginWindow.PluginMainVBox(session)
        self.msn_papylib = None
        if 'msn' in self._session.SERVICES: # only when session is papylib.	
            self.msn_papylib = MSNPapylib(session)
            LIST.append({'stock_id' : 'network-disconnect',
                         'text' : u'Live Messenger'})
    
        list_view          = QListViewMod()
        self.widget_stack = QtGui.QStackedWidget()
        
        lay = QtGui.QHBoxLayout()
        lay.addWidget(list_view)
        lay.addWidget(self.widget_stack)
        self.setLayout(lay)
        
        
        self._list_model = QtGui.QStandardItemModel(list_view)
        select_model = QtGui.QItemSelectionModel(self._list_model, list_view)
        list_view.setModel(self._list_model)
        list_view.setSelectionModel(select_model)
        self._delegate = list_view.itemDelegate()
        
        list_view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        list_view.setIconSize(QtCore.QSize(32, 32))
        list_view.setMovement(QtGui.QListView.Static)
        list_view.setUniformItemSizes(True)
        list_view.setResizeMode    (QtGui.QListView.Adjust)
        list_view.setSizePolicy(QtGui.QSizePolicy.Fixed, 
                               QtGui.QSizePolicy.Expanding)
        for i in LIST:
            item = QtGui.QStandardItem(
                            QtGui.QIcon.fromTheme(i['stock_id']), i['text'])
            self._list_model.appendRow(item)
        
        for page in [self.interface,     self.desktop,     self.sound, 
                     self.notification,  self.theme,       self.extension,
                     BaseTable(1,1),     self.msn_papylib]: 
                     #self.plugins_page instead of BaseTable
            if page:
                self.widget_stack.addWidget(page)
            
        
        list_view.selectionModel().currentRowChanged.connect(
                                                        self._on_row_activated)



    def _on_row_activated(self, new_idx, old_idx):
        '''Callback executed when the user clicks an elemet in the list 
        on the left. Shows the matching preference page in the righ part 
        of the window'''
        # Get information about the row that has been selected
        self.widget_stack.setCurrentIndex(new_idx.row())
        self.widget_stack.currentWidget().on_update()
        
    
    def _present(self):
        '''Does Nothing...'''
        pass






class QListViewMod (QtGui.QListView):
    '''This is a QListView with a modified sizeHint'''
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QListView.__init__(self, parent)
        
    def sizeHint(self):
        '''Returns the size hint. Width and Height are 
        calculated as a weighted average between the the one's
        of the QListView itself and the biggest ones of the 
        elemens in the list'''
        # pylint: disable=C0103
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
    '''This is the base class to create a table to edit preferences'''
    def __init__(self, rows, columns, homogeneous=False, parent=None):
        '''Constructor'''
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
        '''Adds a widget to the table'''
        self.grid_lay.addWidget(widget, row, column, row_span, col_span)
        
    
    def append_row(self, widget, row=None):
        '''Appends a row to the table'''
        increment_current_row = False
        if row == None:
            row = self._current_row
            increment_current_row = True

        self.grid_lay.addWidget(widget, row, 0, 1, self._columns)

        if increment_current_row:
            self._current_row += 1
    
    
    def add_text(self, text, column, row, align_left=False, line_wrap=True):
        '''Adds a label with thext to row and column, align the text left if
        align_left is True'''
        label = QtGui.QLabel(text)
        label.setWordWrap(line_wrap)
        self.add_label(label, column, row, align_left)


    def add_label(self, label, column, row, align_left=False, line_wrap=True):
        '''Adds a label with thext to row and column, align the text left if
        align_left is True'''
        if align_left:
            pass
        label.setWordWrap(line_wrap)
        self.grid_lay.addWidget(label, row, column)
    
    def append_markup(self, text):
        '''Appends a label'''
        label = QtGui.QLabel(text)
        self.append_row(label, None)
        

    def add_button(self, text, column, row, on_click, 
                   xoptions=None, yoptions=None):
        '''Adds a button with text to the row and column, connect the clicked
        event to on_click'''
        button = QtGui.QPushButton(text)
        button.clicked.connect(on_click)
        self.grid_lay.addWidget(button, row, column)
        

    def append_entry_default(self, text, property_name, default):
        '''Append a row with a label and a line_edit, set the value to the
        value of property_name if exists, if not set it to default.
        Add a reset button that sets the value to the default'''

        def on_reset_clicked(entry, default):
            '''called when the reset button is clicked, sets
            entry text to default'''
            entry.setText(default)

        def on_entry_changed(entry, property_name):
            '''Called when the content of an entry changes,
            set the value of the property to the new value'''
            self.set_attr(property_name, unicode(entry.text()))

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
        
        text = self.get_attr(property_name) or default
        line_edit.setText(text)
        
        reset.clicked.connect(
                        lambda: on_reset_clicked(line_edit, default))
        line_edit.textChanged.connect(
                        lambda t: on_entry_changed(line_edit, property_name))


    def append_check(self, text, property_name, row=None):
        '''Append a row with a check box with text as label and
        set the check state with default'''
        # TODO: Inspect if we can put self.on_toggle inside this method.
        widget = QtGui.QCheckBox(text)
        
        self.append_row(widget, row)
        
        default = self.get_attr(property_name)
        widget.setChecked(default)
        
        widget.toggled.connect(
                        lambda checked: self.on_toggled(widget, property_name))
        

    def append_range(self, text, property_name, min_val, max_val, is_int=True):
        '''Append a row with a scale to select an integer value between
        min and max'''
        
        label = QtGui.QLabel(text)
        scale = QtGui.QSlider(Qt.Horizontal)
        spin  = QtGui.QSpinBox()
        
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(label)
        hlay.addWidget(scale)
        hlay.addWidget(spin)
        widget = QtGui.QWidget()
        widget.setLayout(hlay)
        self.append_row(widget, None)
        
        scale.setRange(min_val, max_val)
        spin.setRange(min_val, max_val)
        default = self.get_attr(property_name)
        if default is None:
            default = min_val
        scale.setValue(default)
        spin.setValue(default)

        #if is_int:
        #    scale.set_digits(0)
        
        scale.valueChanged.connect( lambda value: self.on_range_changed(
                                                            scale, 
                                                            property_name,
                                                            is_int))
        scale.valueChanged.connect(spin.setValue)
        spin.valueChanged.connect(scale.setValue)
        

    def append_combo(self, text, getter, property_name):
        '''Append a row with a check box with text as label and
        set the check state with default'''
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
        '''Callback called when the selection of the combo changed
        '''
        self.set_attr(property_name, str(combo.currentText()))


    def on_range_changed(self, scale, property_name, is_int):
        '''Callback called when the selection of the combo changed'''
        value = scale.value()
        if is_int:
            value = int(value)
        self.set_attr(property_name, value)
        

    def on_toggled(self, checkbutton, property_name):
        '''Default callback for a cehckbutton, set property_name
        to the status of the checkbutton'''
        self.set_attr(property_name, checkbutton.isChecked())


    def get_attr(self, name):
        '''Return the value of an attribute, if it has dots, then
        get the values until the last'''

        obj = self
        for attr in name.split('.'):
            obj = getattr(obj, attr)

        return obj

    def set_attr(self, name, value):
        '''Set the value of an attribute, if it has dots, then
        get the values until the last'''

        obj = self
        terms = name.split('.')

        for attr in terms[:-1]:
            obj = getattr(obj, attr)

        setattr(obj, terms[-1], value)
        return obj

    def get_attr_or_default(self, obj, name, default=None):
        '''Try to get the value of the attribute 'name' from obj, if it
        doesn't exist return default'''
        if not hasattr(obj, name):
            return default

        return getattr(obj, name)

    def on_update(self):
        pass
        
    
    def show_all(self):
        pass





class Interface(BaseTable):
    '''the panel to display/modify the config related to the gui
    '''

    def __init__(self, session):
        '''constructor
        '''
        BaseTable.__init__(self, 4, 1)
        self.session = session
        self.append_markup('<b>'+tr('Main window:')+'</b>')
        self.append_check(tr('Show user panel'),
            'session.config.b_show_userpanel')
        self.append_markup('<b>'+tr('Conversation window:')+'</b>')
        self.session.config.get_or_set('b_avatar_on_left', False)
        self.session.config.get_or_set('b_toolbar_small', False)
        self.append_check(tr('Start minimized/iconified'), 
                           'session.config.b_conv_minimized')
        self.append_check(tr('Show emoticons'), 
                           'session.config.b_show_emoticons')
        self.append_check(tr('Show conversation header'),
            'session.config.b_show_header')
        self.append_check(tr('Show conversation side panel'),
            'session.config.b_show_info')
        self.append_check(tr('Show conversation toolbar'),
            'session.config.b_show_toolbar')
        self.append_check(tr('Small conversation toolbar'),
            'session.config.b_toolbar_small')
        self.append_check(tr('Avatar on conversation left side'),
            'session.config.b_avatar_on_left')
        self.append_check(tr('Allow auto scroll in conversation'),
            'session.config.b_allow_auto_scroll')
        self.append_check(tr('Enable spell check if available (requires %s)') % \
                                                            'python-gtkspell',
            'session.config.b_enable_spell_check')

        self.append_range(tr('Contact list avatar size'),
            'session.config.i_avatar_size', 18, 64)
        self.append_range(tr('Conversation avatar size'),
            'session.config.i_conv_avatar_size', 18, 128)





class Desktop(BaseTable):
    ''' This panel contains some desktop related settings '''

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 3, 2)
        self._session = session

        self.append_markup('<b>'+tr('File transfers')+'</b>')
        self.append_check(tr('Sort received files by sender'), 
                          '_session.config.b_download_folder_per_account')
        self.add_text(tr('Save files to:'), 0, 2, True)

        def on_path_button_clicked():
            ''' updates the download dir config value '''
            new_path = unicode(QtGui.QFileDialog.getExistingDirectory(
                            directory = self._session.config.download_folder))
            set_new_path(new_path)
            path_edit.setText(new_path)
        
        def set_new_path(new_path):
            if new_path != self._session.config.download_folder:
                self._session.config.download_folder = new_path
            
        path_edit = QtGui.QLineEdit(
            self._session.config.get_or_set("download_folder", 
                                           e3.common.locations.downloads()))
        path = QtGui.QWidget()
        path_button = QtGui.QPushButton( QtGui.QIcon.fromTheme('folder'), '')
        path_lay = QtGui.QHBoxLayout()
        path_lay.addWidget(path_edit)
        path_lay.addWidget(path_button)
        path.setLayout(path_lay)
        self.attach(path, 2, 3, 2, 3)
        
        path_button.clicked.connect(on_path_button_clicked)
        path_edit.textChanged.connect(
                            lambda new_path: set_new_path(unicode(new_path)))
        self.show_all()
        
        
        
        

class Sound(BaseTable):
    '''the panel to display/modify the config related to the sounds
    '''

    def __init__(self, session):
        '''constructor
        '''
        BaseTable.__init__(self, 6, 1)
        self.session = session
        self.append_markup('<b>'+tr('Messages events:')+'</b>')
        self.append_check(tr('Mute sounds'),
            'session.config.b_mute_sounds')
        self.append_check(tr('Play sound on sent message'),
            'session.config.b_play_send')
        self.append_check(tr('Play sound on first received message'),
            'session.config.b_play_first_send')
        self.append_check(tr('Play sound on received message'),
            'session.config.b_play_type')
        self.append_check(tr('Play sound on nudge'),
            'session.config.b_play_nudge')

        self.append_markup('<b>'+tr('Users events:')+'</b>')
        self.append_check(tr('Play sound on contact online'),
            'session.config.b_play_contact_online')
        self.append_check(tr('Play sound on contact offline'),
            'session.config.b_play_contact_offline')





class Notification(BaseTable):
    '''the panel to display/modify the config related to the notifications
    '''

    def __init__(self, session):
        '''constructor
        '''
        BaseTable.__init__(self, 2, 1)
        self.session = session
        self.append_check(tr('Notify on contact online'),
            'session.config.b_notify_contact_online')
        self.append_check(tr('Notify on contact offline'),
            'session.config.b_notify_contact_offline')
        self.append_check(tr('Notify on received message'),
            'session.config.b_notify_receive_message')





class Theme(BaseTable):
    '''the panel to display/modify the config related to the theme
    '''

    def __init__(self, session):
        '''constructor
        '''
        BaseTable.__init__(self, 5, 1)
        self.session = session

        contact_list_cls = extension.get_default('contact list')

        adium_theme = self.session.config.get_or_set('adium_theme', 'renkoo')

        self.append_combo(tr('Image theme'), gui.theme.get_image_themes,
            'session.config.image_theme')
        self.append_combo(tr('Sound theme'), gui.theme.get_sound_themes,
            'session.config.sound_theme')
        self.append_combo(tr('Emote theme'), gui.theme.get_emote_themes,
            'session.config.emote_theme')
        self.append_combo(tr('Adium theme'), gui.theme.get_adium_themes,
            'session.config.adium_theme')
        self.append_entry_default(tr('Nick format'),
                'session.config.nick_template', contact_list_cls.NICK_TPL)
        self.append_entry_default(tr('Group format'),
                'session.config.group_template', contact_list_cls.GROUP_TPL)





class Extension(BaseTable):
    '''the panel to display/modify the config related to the extensions_cmb
    '''

    def __init__(self, session):
        '''constructor
        '''
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
        '''add the widgets that will display the information of the 
        extension category and the selected extension and widgets 
        to display the extensions'''
        
        self.add_text(tr('Categories'),  0, 0, True)
        self.add_text(tr('Selected'),    0, 1, True)
        self.add_text('',              0, 2, True)
        self.add_text(tr('Name'),        0, 3, True)
        self.add_text(tr('Description'), 0, 4, True)
        self.add_text(tr('Author'),      0, 5, True)
        self.add_text(tr('Website'),     0, 6, True)
        self.add_label(self.name_info,        1, 3, True)
        self.add_label(self.description_info, 1, 4, True)
        self.add_label(self.author_info,      1, 5, True)
        self.add_label(self.website_info,     1, 6, True)
        self.add_button(tr('Redraw main screen'), 1, 7,
                self._on_redraw_main_screen)
        self.attach(self.categories_cmb, 1, 2, 0, 1)
        self.attach(self.extensions_cmb, 1, 2, 1, 2)
        
        categories = self._get_categories()
        for item in categories:
            log.info('category item: %s' % item)
            self.categories_cmb.addItem(item)
        self.categories_cmb.setCurrentIndex(0)
        self._on_category_changed(self.categories_cmb)
        
        self.categories_cmb.currentIndexChanged.connect(
                lambda text: self._on_category_changed(self.categories_cmb))
        self.extensions_cmb.currentIndexChanged.connect(
                lambda text: self._on_extension_changed(self.extensions_cmb))
        
        
    def _on_redraw_main_screen(self, button):
        '''called when the Redraw main screen button is clicked'''
        self._session.save_config()
        self._session.signals.login_succeed.emit()
        self._session.signals.contact_list_ready.emit()


    def _on_category_changed(self, combo):
        '''callback called when the category on the combo changes'''
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
        '''callback called when the extension on the combo changes'''
        category = str(self.categories_cmb.currentText())
        extension_index = self.extensions_cmb.currentIndex()

        # when the model is cleared this event is emited
        if extension_index == -1:
            return
        
        ext, identifier = self.extension_list[extension_index]
        if not extension.set_default_by_id(category, identifier):
            # TODO: revert the selection to the previous selected extension
            log.warning(('Could not set %s as default extension for %s') % \
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
        '''fill the information about the ext'''
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
        categories = [ctg for ctg in extension.get_categories().keys() \
                      if len(extension.get_extensions(ctg)) > 1]
        categories.sort()
        return categories
        
        
        
class MSNPapylib(BaseTable):
    ''' This panel contains some msn-papylib specific settings '''

    def __init__(self, session):
        '''constructor
        '''
        BaseTable.__init__(self, 8, 2)
        self.session = session

        self.add_text(tr('If you have problems with your nickname/message/\n'
                        'picture just click on this button, sign in with \n'
                        'your account and load a picture in your Live Profile.'
                        '\nThen restart emesene and have fun.'), 0, 0, True)
        self.add_button(tr('Open Live Profile'), 1, 0, 
                        self._on_live_profile_clicked, 0, 0)


    def _on_live_profile_clicked(self, arg):
        ''' called when live profile button is clicked '''
        webbrowser.open("http://profile.live.com/details/Edit/Pic")
