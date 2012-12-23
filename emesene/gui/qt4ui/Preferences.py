# -*- coding: utf-8 -*-

'''This module contains classes used to build up a Preferences window'''

import logging

from PyQt4  import QtGui
from PyQt4  import QtCore
from PyQt4.QtCore import Qt

from gui.qt4ui.Utils import tr

import e3.common
import extension
import gui
import sys
from Language import Language, get_language_manager

try:
    from enchant_dicts import list_dicts
except:
    def list_dicts():
        return []

log = logging.getLogger('qt4ui.Preferences')

LIST = [
    {'stock_id' : 'preferences-desktop',               'text' : tr('General'  )},
    {'stock_id' : 'preferences-desktop-accessibility', 'text' : tr('Main Window')},
    {'stock_id' : 'preferences-desktop-accessibility', 'text' : tr('Conversation Window')},
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
        self.setWindowIcon(QtGui.QIcon(gui.theme.image_theme.logo))
        self.resize(600, 400)
        
        self._session = session
        #TODO: check
        self.session = session
        self.general      = GeneralTab(session)
        self.main = MainWindow(session)
        self.conversation = ConversationWindow(session)
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
        
        for page in [self.general, self.main, self.conversation,     self.sound, 
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
        
    
    def remove_subscriptions(self):
        '''RemovesNothing...'''
        pass
    
    def present(self):
        '''Does Nothing...'''
        pass

    def check_for_updates(self):
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
        self._current_row += 1

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
        
    def append_entry_default(self, text, format_type,
                             property_name, default, tooltip_text,
                             has_help=True, has_apply=False):
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

        def on_help_clicked(button, format_type):
            """called when the help button is clicked"""
            extension.get_default('dialog').contactlist_format_help(format_type)

        def on_apply_clicked(button, entry, property_name):
            """called when the apply button is clicked"""
            on_entry_changed(entry, property_name)

        label = QtGui.QLabel(text)
        line_edit = QtGui.QLineEdit()
        reset = QtGui.QPushButton(QtGui.QIcon.fromTheme('edit-clear'), '')
        
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(label)
        hlay.addStretch()
        hlay.addWidget(line_edit)
        row = QtGui.QWidget()
        row.setLayout(hlay)
        self.append_row(row)
        
        text = self.get_attr(property_name) or default
        line_edit.setText(text)
        
        reset.clicked.connect(
                        lambda checked: on_reset_clicked(line_edit, default))
        if has_apply:
            entry_apply = QtGui.QPushButton('')
            hlay.addWidget(entry_apply)
            entry_apply.setText(tr('Apply'))
            entry_apply.toggled.connect(
                            lambda checked: on_apply_clicked(entry_apply, entry, property_name))
            line_edit.returnPressed.connect( lambda self: on_entry_changed(line_edit, property_name))
        else:
            line_edit.textChanged.connect(
                            lambda text: on_entry_changed(line_edit, property_name))

        hlay.addWidget(reset)

        if has_help:
            help = QtGui.QPushButton(QtGui.QIcon.fromTheme('system-help'), '')
            hlay.addWidget(help)
            help.setToolTip(tooltip_text)
            help.clicked.connect(
                        lambda: on_help_clicked(help, format_type))

    def create_check(self, text, property_name):
        """create a CheckButton and
        set the check state with default
        """
        default = self.get_attr(property_name)
        widget = QtGui.QCheckBox(text)
        widget.setChecked(default)
        widget.toggled.connect(
                        lambda checked: self.on_toggled(widget, property_name))
        return widget

    def append_check(self, text, property_name, row=None):
        '''Append a row with a check box with text as label and
        set the check state with default'''
        # TODO: Inspect if we can put self.on_toggle inside this method.
        widget = self.create_check(text, property_name)
        self.append_row(widget, row)
    	return widget

    def append_range(self, text, property_name, min_val, max_val, is_int=True, marks=[]):
        '''Append a row with a scale to select an integer value between
        min and max'''
        
        label = QtGui.QLabel(text)
        scale = QtGui.QSlider(Qt.Horizontal)
        #QT supports mark in intervals so use first value
        for mark in marks:
            scale.setTickInterval(mark)
            break
        scale.setTickPosition(QtGui.QSlider.TicksBelow)
        spin = QtGui.QSpinBox()
        
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

    def fill_combo(self, combo, getter, property_name, values=None):
        if values:
            default = getter()[values.index(self.get_attr(property_name))]
        else:
            default = self.get_attr(property_name)

        count = 0
        default_count = 0
        for item in getter():
            combo.addItem(item)
            if item == default:
                default_count = count
            count += 1
        combo.setCurrentIndex(default_count)

    def create_combo (self, getter, property_name,
                      values=None, changed_cb = None):

        combo = QtGui.QComboBox()
        self.fill_combo(combo, getter, property_name, values)
        if changed_cb:
            combo.currentIndexChanged.connect(lambda text: changed_cb(combo, property_name))
        else:
            combo.currentIndexChanged.connect(
            	lambda text: self.on_combo_changed(combo, property_name))
        return combo

    def create_combo_with_label(self, text,
                                getter, property_name,
                                values=None, changed_cb = None):
        """creates and return a new ComboBox with a label and append
           values to the combo
        """
        label = QtGui.QLabel(text)
        combo = self.create_combo(getter, property_name, values)
        
        hlay = QtGui.QHBoxLayout()
        hlay.addWidget(label)
        hlay.addWidget(combo)
        widget = QtGui.QWidget()
        widget.setLayout(hlay)

        return widget

    def append_combo(self, text, getter, property_name, values=None):
        '''Append a row with a check box with text as label and
        set the check state with default'''
        widget = self.create_combo_with_label(text, getter, property_name, values)
        self.append_row(widget, None)

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


class GeneralTab(BaseTable):
    ''' This panel contains some desktop related settings '''

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 4, 2)
        self.session = session

        self.append_markup('<b>'+tr('Logger')+'</b>')
        self.append_check(tr('Enable logger'),
                          'session.config.b_log_enabled')

        # language settings
        self.append_markup('<b>'+tr('Language')+'</b>')
        # languages combobox
        self._language_management = get_language_manager()

        self.session.config.subscribe(self._on_language_changed,
                                      'language_config')

        self.add_text(tr("Select language:"), 0, 3,  True)

        #language option
        self.session.config.get_or_set("spell_lang", "en")
        self.lang_menu = self.create_combo(self.get_spell_langs, 'session.config.spell_lang')

        cb_check_spelling = self.create_check(
            tr('Enable spell check if available \n(requires %s)')
            % 'python-gtkspell',
            'session.config.b_enable_spell_check')

        self.append_row(cb_check_spelling)
        self.attach(self.lang_menu, 2, 5, 4, 1)#, gtk.FILL, 0)

        self.session.config.subscribe(self._on_spell_change,
            'b_enable_spell_check')

        #update spell lang combo sensitivity
        self._on_spell_change(self.session.config.get_or_set('b_enable_spell_check', False))

        self.append_markup('<b>'+tr('File transfers')+'</b>')
        self.append_check(tr('Sort received files by sender'), 
                          'session.config.b_download_folder_per_account')
        self.append_markup(tr('Save files to:'))

        def on_path_button_clicked():
            ''' updates the download dir config value '''
            new_path = unicode(QtGui.QFileDialog.getExistingDirectory(
                            directory = self.session.config.download_folder))
            set_new_path(new_path)
            path_edit.setText(new_path)
        
        def set_new_path(new_path):
            if new_path != self.session.config.download_folder:
                self.session.config.download_folder = new_path
            
        path_edit = QtGui.QLineEdit(
            self.session.config.get_or_set("download_folder", 
                                           e3.common.locations.downloads()))
        path = QtGui.QWidget()
        path_button = QtGui.QPushButton( QtGui.QIcon.fromTheme('folder'), '')
        path_lay = QtGui.QHBoxLayout()
        path_lay.addWidget(path_edit)
        path_lay.addWidget(path_button)
        path.setLayout(path_lay)
        self.attach(path, 5, 3, 7, 1)
        
        path_button.clicked.connect(on_path_button_clicked)
        path_edit.textChanged.connect(
                            lambda new_path: set_new_path(unicode(new_path)))

        # mail settings
        self.append_markup('<b>'+_('Mail')+'</b>')
        self.append_check(_('Open mail in default desktop client'),
                          'session.config.b_open_mail_in_desktop')

        self.append_markup('<b>'+_('Updates')+'</b>')
        self.append_check(_('Weekly check for plugins/themes updates on startup'),
                          'session.config.b_check_for_updates')

        self.show_all()

    def _on_language_changed(self,  lang):
        self._language_management.install_desired_translation(lang)

    def get_spell_langs(self):
        return sorted(set(list_dicts()))

    def _on_spell_change(self, value):
#        self.lang_menu.set_sensitive(value)
        pass


class MainWindow(BaseTable):
    """the panel to display/modify the config related to the gui
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 17, 2)
        self.session = session

        ContactList = extension.get_default('contact list')

        self.append_markup('<b>'+tr('User panel:')+'</b>')
        self.append_check(_('Show user panel'),
            'session.config.b_show_userpanel')
        self.append_check(tr('Show unread mail count'),
            'session.config.b_show_mail_inbox')
        self.append_markup('<b>'+tr('Contact list:')+'</b>')
        avatar_size = self.append_range(tr('Contact list avatar size'),
            'session.config.i_avatar_size', 18, 64, marks=[32, 48])

        self.append_entry_default(tr('Nick format'), 'nick',
                                  'session.config.nick_template_clist',
                                  ContactList.NICK_TPL, tr('Nick Format Help'),
                                  has_apply=True)
        self.append_entry_default(tr('Group format'), 'group',
                                  'session.config.group_template',
                                  ContactList.GROUP_TPL, tr('Group Format Help'),
                                  has_apply=True)

        if sys.platform == 'darwin':

            def do_hideshow(widget):
                if widget.getChecked():
                    subprocess.call('defaults write '
                                    '/Applications/emesene.app/Contents/Info'
                                    ' LSUIElement -bool false', shell=True)
                else:
                    subprocess.call('defaults write '
                                    '/Applications/emesene.app/Contents/Info'
                                    ' LSUIElement -bool true', shell=True)

            self.append_markup('<b>'+tr('OS X Integration:')+'</b>')
            self.session.config.get_or_set('b_show_dock_icon', True)

            button = self.append_check(tr('Show dock icon '
                                       '(requires restart of emesene)'),
                                       'session.config.b_show_dock_icon')
            button.toggled.connect(
                        lambda checked: do_hideshow(widget, property_name))
            self.session.config.get_or_set('b_hide_menu', False)
            button = self.append_check(tr('Hide menu'),
                                       'session.config.b_hide_menu')
        self.show_all()


class ConversationWindow(BaseTable):
    """the panel to display/modify the config related to the gui
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 17, 1)
        self.session = session

        # override text color option

        cb_override_text_color = self.create_check(
                                        tr('Override incoming text color'),
                                        'session.config.b_override_text_color')

        self.session.config.subscribe(self._on_cb_override_text_color_toggled,
            'b_override_text_color')

        def on_color_selected(cb):
            col = cb.get_color()
            col_e3 = e3.base.Color(col.red, col.green, col.blue)
            self.set_attr('session.config.override_text_color',
                          '#'+col_e3.to_hex())

#FIXME:
#        self.b_text_color = gtk.ColorButton(color=gtk.gdk.color_parse(
#                            self.get_attr('session.config.override_text_color')))
#        self.b_text_color.set_use_alpha(False)
#        self.b_text_color.connect('color-set', on_color_selected)
#        h_color_box = gtk.HBox()
#        h_color_box.pack_start(cb_override_text_color)
#        h_color_box.pack_start(self.b_text_color)

        # preference list

        self.session.config.get_or_set('i_tab_position', 0)
        self.tab_pos_cb = self.create_combo_with_label(tr('Tab position'),
            self.get_tab_positions, 'session.config.i_tab_position',range(4))

        self.int_mode = 2
        if session.config.b_single_window:
            self.int_mode = 0
        elif session.config.b_conversation_tabs:
            self.int_mode = 1

        self.integrated_mode_cb = self.create_combo_with_label(tr('Integrated mode'),
            self.get_integrated_mode, 'int_mode', range(3),
            self._on_integrated_mode_change)

        self.session.config.get_or_set('b_avatar_on_left', False)
        self.session.config.get_or_set('b_toolbar_small', False)
        self.session.config.get_or_set('b_escape_hotkey', True)
        self.session.config.get_or_set('b_close_button_on_tabs', True)
        self.session.config.get_or_set('b_show_avatar_in_taskbar', True)

        self.append_markup('<b>'+tr('Layout')+'</b>')
        self.append_row(self.integrated_mode_cb)
        self.append_row(self.tab_pos_cb)
        self.append_check(tr('Show conversation header'),
            'session.config.b_show_header')
        self.append_check(tr('Show conversation toolbar'),
            'session.config.b_show_toolbar')
        self.append_check(tr('Show close button on tabs'),
            'session.config.b_close_button_on_tabs')
        # Avatar-on-left sensitivity depends on side panel visibility
        self.cb_avatar_left = self.create_check(tr('Avatar on conversation left side'),
            'session.config.b_avatar_on_left')
        self.append_row(self.cb_avatar_left)

        self.append_markup('<b>'+tr('Appearance')+'</b>')
        self.append_check(tr('Show emoticons'),
                          'session.config.b_show_emoticons')
        self.append_check(tr('Show avatars in taskbar instead of status icons'),
            'session.config.b_show_avatar_in_taskbar')

#        self.append_row(h_color_box)

        #update ColorButton sensitive
        self._on_cb_override_text_color_toggled(
                self.session.config.get_or_set('b_override_text_color', False))

        avatar_size = self.append_range(tr('Conversation avatar size'),
            'session.config.i_conv_avatar_size', 18, 128, marks=[32,64,96])

        self.append_markup('<b>'+tr('Behavior')+'</b>')
        self.append_check(tr('Start minimized/iconified'),
                          'session.config.b_conv_minimized')
        self.append_check(tr('Enable escape hotkey to close tabs'),
            'session.config.b_escape_hotkey')
        self.append_check(tr('Allow auto scroll in conversation'),
            'session.config.b_allow_auto_scroll')

        self.show_all()

    def get_tab_positions(self):
        return [tr("Top"), tr("Bottom"), tr("Left"), tr("Right")]

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_cb_override_text_color_toggled,
            'b_override_text_color')

    def _on_cb_override_text_color_toggled(self, value):
        #self.b_text_color.setEnabled(value)
        pass

    def _on_integrated_mode_change(self, combo, property_name, value):
        self.int_mode = combo.get_active()
        if self.int_mode == 0:
            self.session.config.b_single_window = True
            self.session.config.b_conversation_tabs = True
        elif self.int_mode == 1:
            self.session.config.b_single_window = False
            self.session.config.b_conversation_tabs = True
        else:
            self.session.config.b_single_window = False
            self.session.config.b_conversation_tabs = False
        self.tab_pos_cb.set_sensitive(self.session.config.b_conversation_tabs)

    def get_integrated_mode(self):
        return [tr("Single Window"),
                tr("Tabbed Conversations"),
                tr("Multiple Conversations")]


class Sound(BaseTable):
    """the panel to display/modify the config related to the sounds
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 7, 1)
        self.session = session
        self.array = []
        self.append_markup('<b>'+tr('General:')+'</b>')
        self.mute_sound = self.append_check(_('Mute sounds'),
            'session.config.b_mute_sounds')
        self.append_markup('<b>'+tr('Users events:')+'</b>')
        self.array.append(self.append_check(tr('Play sound on contact online'),
            'session.config.b_play_contact_online'))
        self.array.append(self.append_check(tr('Play sound on contact offline'),
            'session.config.b_play_contact_offline'))
        self.append_markup('<b>'+tr('Messages events:')+'</b>')
        self.array.append(self.append_check(tr('Play sound on sent message'),
            'session.config.b_play_send'))
        self.array.append(self.append_check(tr('Play sound on first received message'),
            'session.config.b_play_first_send'))
        self.array.append(self.append_check(tr('Play sound on received message'),
            'session.config.b_play_type'))
        self.array.append(self.append_check(tr('Play sound on nudge'),
            'session.config.b_play_nudge'))
        self.array.append(self.append_check(tr('Mute sounds when the conversation has focus'),
            'session.config.b_mute_sounds_when_focussed'))

        self._on_mute_sounds_changed(self.session.config.b_mute_sounds)

        self.session.config.subscribe(self._on_mute_sounds_changed,
            'b_mute_sounds')

        self.show_all()

    def _on_mute_sounds_changed(self, value):
        self.mute_sound.setChecked(value)
        for i in self.array:
            i.setEnabled(not value)

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_mute_sounds_changed,
            'b_mute_sounds')


class Notification(BaseTable):
    """the panel to display/modify the config related to the notifications
    """

    def __init__(self, session):
        """constructor
        """
        BaseTable.__init__(self, 4, 1)
        self.session = session
        self.array = []

        self.append_markup('<b>'+tr('General:')+'</b>')
        self.append_check(tr('Mute notifications'),
            'session.config.b_mute_notification')
        self.array.append(self.append_check(tr('Only when available'),
            'session.config.b_notify_only_when_available'))
        self.append_markup('<b>'+tr('Users events:')+'</b>')
        self.array.append(self.append_check(tr('Notify on contact online'),
            'session.config.b_notify_contact_online'))
        self.array.append(self.append_check(tr('Notify on contact offline'),
            'session.config.b_notify_contact_offline'))
        self.append_markup('<b>'+tr('Messages events:')+'</b>')
        self.array.append(self.append_check(tr('Notify on received message'),
            'session.config.b_notify_receive_message'))
        self.array.append(self.append_check(tr('Notify when a contact is typing'),
            'session.config.b_notify_typing'))
        self.array.append(self.append_check(tr('Notify also when the conversation has focus'),
            'session.config.b_notify_when_focussed'))
        if self.session and self.session.session_has_service(e3.Session.SERVICE_ENDPOINTS):
            self.append_markup('<b>'+tr('Security events:')+'</b>')
            self.array.append(self.append_check(tr('Notify when signed in from another location'),
                'session.config.b_notify_endpoint_added'))
            self.array.append(self.append_check(tr('Notify when information of signed in location is changed'),
                'session.config.b_notify_endpoint_updated'))

        self._on_mute_notification_changed(self.session.config.b_mute_notification)

        self.session.config.subscribe(self._on_mute_notification_changed,
            'b_mute_notification')

        self.show_all()

    def _on_mute_notification_changed(self, value):
        for i in self.array:
            i.setEnabled(not value)

    def remove_subscriptions(self):
        self.session.config.unsubscribe(self._on_mute_notification_changed,
            'b_mute_notification')


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
        
        categories = extension.get_multiextension_categories()
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
        categories = extension.get_multiextension_categories()
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
        profile_url = self.session.get_worker().profile_url
        gui.base.Desktop.open(profile_url)
