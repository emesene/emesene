# -*- coding: utf-8 -*-

'''a module that defines the api of objects that display dialogs'''

import logging

from PyQt4  import QtCore
from PyQt4  import QtGui
from PyQt4.QtCore  import Qt

from gui.qt4ui import Utils
from gui.qt4ui.Utils import tr

import gui
import extension

log = logging.getLogger('qt4ui.Dialog')

class Dialog(object):
    '''a class full of static methods to handle dialogs, dont instantiate it'''
    NAME = 'Dialog'
    DESCRIPTION = 'Class to show all the dialogs of the application'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''

    @classmethod
    def broken_profile(cls, close_cb, url):
        '''a dialog that asks you to fix your profile'''
        message = _('''\
Your live profile seems to be broken,
which will cause you to experience issues
with your display name, picture
and/or personal message.

You can fix it now by re-uploading
your profile picture on the
Live Messenger website that will open,
or you can choose to fix it later.
To fix your profile, emesene must be closed.
Clicking Yes will close emesene.

Do you want to fix your profile now?''')
        gui.base.Desktop.open(url)

        reply = QtGui.QMessageBox.warning(None, _("You have a broken profile"),
                                          message, QtGui.QMessageBox.Yes |
                                          QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            close_cb()

    @classmethod
    def add_contact(cls, groups, group_selected, response_cb,
                    title="Add user"):
        '''show a dialog asking for an user address, and (optional)
        the group(s) where the user should be added, the response callback
        receives the response type (stock.ADD, stock.CANCEL or stock.CLOSE)
        the account and a tuple of group names where the user should be
        added (give a empty tuple if you don't implement this feature,
        the controls are made by the callback, you just ask for the email,
        don't make any control, you are just implementing a GUI! :P'''
        log.info(str(response_cb))
        dialog      = OkCancelDialog(title)
        text_label  = QtGui.QLabel(tr('E-mail:'))
        text_edit   = QtGui.QLineEdit()
        group_label = QtGui.QLabel(tr('Group:'))
        group_combo = QtGui.QComboBox()

        lay = QtGui.QGridLayout()
        lay.addWidget(text_label, 0, 0)
        lay.addWidget(text_edit, 0, 1)
        lay.addWidget(group_label, 1, 0)
        lay.addWidget(group_combo, 1, 1)
        dialog.setLayout(lay)

        dialog.set_accept_response(gui.stock.ADD)
        text_label.setAlignment(Qt.AlignRight |
                                Qt.AlignVCenter)
        group_label.setAlignment(Qt.AlignRight |
                                 Qt.AlignVCenter)
        dialog.setMinimumWidth(300)

        log.debug(str(groups))
        groups = list(groups)
        log.debug(groups)
        groups.sort()

        group_combo.addItem('<i>' + tr('No Group') + '</i>', '')
        for group in groups:
            group_combo.addItem(group.name, group.name)

        response = dialog.exec_()

        email = unicode(text_edit.text())
        group = group_combo.itemData(group_combo.currentIndex()).toPyObject()
        log.debug('[%s,%s]' % (email, group))
        response_cb(response, email, group)

    @classmethod
    def add_group(cls, response_cb, title=tr('Add group')):
        '''show a dialog asking for a group name, the response callback
        receives the response (stock.ADD, stock.CANCEL, stock.CLOSE)
        and the name of the group, the control for a valid group is made
        on the controller, so if the group is empty you just call the
        callback, to make a unified behaviour, and also, to only implement
        GUI logic on your code and not client logic
        cb args: response, group_name'''
        log.debug(str(response_cb))
        dialog = OkCancelDialog(title)
        group_label = QtGui.QLabel(tr('New group\'s name:'))
        group_edit  = QtGui.QLineEdit()

        lay = QtGui.QHBoxLayout()
        lay.addWidget(group_label)
        lay.addWidget(group_edit)
        dialog.setLayout(lay)

        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(380)

        response = dialog.exec_()

        group_name = unicode(group_edit.text())

        response_cb(response, group_name)

    @classmethod
    def rename_group(cls, group, response_cb, title=tr('Rename group')):
        '''show a dialog with the group name and ask to rename it, the
        response callback receives stock.ACCEPT, stock.CANCEL or stock.CLOSE
        the old and the new name.
        cb args: response, group, new_name
        '''
        dialog = EntryDialog(tr('New group name:'), group.name, title)
        response = dialog.exec_()
        response_cb(response, group, dialog.text())

    @classmethod
    def contact_added_you(cls, accounts, response_cb,
                          title=tr("User invitation")):
        '''show a dialog displaying information about users
        that added you to their userlists, the accounts parameter is
        a tuple of mail, nick that represent all the users that added you,
        the way you confirm (one or more dialogs) doesn't matter, but
        you should call the response callback only once with a dict
        with two keys 'accepted' and 'rejected' and a list of mail
        addresses as values
        '''
        def debug_response_cb(results):
            '''Simply prints the results instead of invocating the
            real response_cb'''
            print results
        dialog = ContactAddedYouDialog(accounts, response_cb, title)

    @classmethod
    def crop_image(cls, response_cb, filename, title=tr('Select image area')):
        '''Shows a dialog to select a portion of an image.'''
        dialog = OkCancelDialog(title, expanding=True)

        # Actions
        act_dict = {}
        act_dict['rotate_left'] = QtGui.QAction(tr('Rotate Left'), dialog)
        act_dict['rotate_right'] = QtGui.QAction(tr('Rotate right'), dialog)
        act_dict['fit_zoom']     = QtGui.QAction(tr('Zoom to fit'), dialog)
        act_dict['fit_zoom']     = QtGui.QAction(tr('Zoom to fit'), dialog)
        act_dict['reset_zoom']   = QtGui.QAction(tr('Reset zoom'), dialog)
        act_dict['select_all']   = QtGui.QAction(tr('Select All'), dialog)
        act_dict['select_unsc']  = QtGui.QAction(tr('Select Unscaled'), dialog)

        # widgets
        toolbar = QtGui.QToolBar()
        scroll_area = QtGui.QScrollArea()
        area_selector = extension.get_and_instantiate(
                                                      'image area selector', QtGui.QPixmap(filename))

        # layout
        lay = QtGui.QVBoxLayout()
        lay.addWidget(toolbar)
        lay.addWidget(scroll_area)
        dialog.setLayout(lay)

        # widget setup
        toolbar.addAction(act_dict['rotate_left'])
        toolbar.addAction(act_dict['rotate_right'])
        toolbar.addSeparator()
        toolbar.addAction(act_dict['fit_zoom'])
        toolbar.addAction(act_dict['reset_zoom'])
        toolbar.addSeparator()
        toolbar.addAction(act_dict['select_all'])
        toolbar.addAction(act_dict['select_unsc'])
        scroll_area.setWidget(area_selector)
        scroll_area.setWidgetResizable(True)

        # Signal connection:
        act_dict['rotate_left'].triggered.connect(area_selector.rotate_left)
        act_dict['rotate_right'].triggered.connect(area_selector.rotate_right)
        act_dict['fit_zoom'].triggered.connect(area_selector.fit_zoom)
        act_dict['reset_zoom'].triggered.connect(
                                                 lambda: area_selector.set_zoom(1))
        act_dict['select_all'].triggered.connect(area_selector.select_all)
        act_dict['select_unsc'].triggered.connect(
                                                  area_selector.select_unscaled)
        # test:
        if (False):
            preview = QtGui.QLabel()
            lay.addWidget(preview)
            area_selector.selection_changed.connect(
                                                    lambda: preview.setPixmap(area_selector.get_selected_pixmap()))

            zoom_sli = QtGui.QSlider(Qt.Horizontal)
            zoom_sli.setMinimum(1)
            zoom_sli.setMaximum(40)
            zoom_sli.setValue(20)
            zoom_sli.setSingleStep(1)
            lay.addWidget(zoom_sli)
            zoom_sli.valueChanged.connect(
                                          lambda z:area_selector.set_zoom(z / 10.0))
        # Dialog execution:
        response = dialog.exec_()

        selected_pixmap = area_selector.get_selected_pixmap()

        response_cb(response, selected_pixmap)

    @classmethod
    def error(cls, message, response_cb=None, title=tr('Error!')):
        '''show an error dialog displaying the message, this dialog should
        have only the option to close and the response callback is optional
        since in few cases one want to know when the error dialog was closed,
        but it can happen, so return stock.CLOSE to the callback if its set'''
        # TODO: Consider an error notification like dolphin's notifications
        # and or consider desktop integration with windows.
        # TODO: Consider making a more abstract class to use as a base for
        # every kind of message box: error, info, attention, etc...
        dialog  = StandardButtonDialog(title)
        icon    = QtGui.QLabel()
        message = QtGui.QLabel(unicode(message))

        lay = QtGui.QHBoxLayout()
        lay.addWidget(icon)
        lay.addWidget(message)
        dialog.setLayout(lay)

        dialog.add_button(QtGui.QDialogButtonBox.Ok)
        dialog.setMinimumWidth(250)
#        dialog.setSizeGripEnabled(False)
#        dialog.setSizePolicy(QtGui.QSizePolicy.Fixed,
#                             QtGui.QSizePolicy.Fixed)
    #dialog.setModal(True)
#        dialog.setWindowModality(Qt.WindowModal)
        icon.setPixmap(QtGui.QIcon.fromTheme('dialog-error').pixmap(64, 64))
        message.setAlignment(Qt.AlignCenter)
        dialog.exec_()

    @classmethod
    def login_preferences(cls, service, service_host, service_port,
                          callback, use_http, use_ipv6, proxy):
        """
        display the preferences dialog for the login window

        cls -- the dialog class
        service -- the service string identifier (for example 'gtalk')
        callback -- callback to call if the user press accept, call with the
            new values
        use_http -- boolean that indicates if the e3 should use http
            method
        use_ipv6 -- boolean that indicates if the xmpp should use ipv6
            to established connection
        proxy -- a e3.Proxy object
        """
        def on_session_changed(*args):
            '''Callback called when the session type in the combo is
            called'''
            service = str(session_cmb.currentText())
            session_id, ext = name_to_ext[service]
            server_host_edit.setText(ext.SERVICES[service]['host'])
            server_port_edit.setText(ext.SERVICES[service]['port'])

        def on_use_auth_toggled(is_enabled, is_checked):
            '''called when the auth check button is toggled, receive a set
            of entries, enable or disable auth related widgets deppending
            on the state of the check button'''
            auth_settings = (user_lbl, user_edit, pwd_lbl, pwd_edit)
            state = (is_enabled and is_checked)
            for widget in auth_settings:
                widget.setEnabled(state)

        def on_use_proxy_toggled(is_checked, *args):
            '''Callback invoked when the 'use proxy' checkbox is toggled.
            enables or disables widgets to insert proxy settings accordingly'''
            proxy_settings = (host_lbl, proxy_host_edit, port_lbl,
                              proxy_port_edit, auth_chk)
            log.info('upt')
            for widget in proxy_settings:
                widget.setEnabled(is_checked)
            on_use_auth_toggled(is_checked, auth_chk.isChecked())

        def response_cb(response):
            '''called on any response (close, accept, cancel) if accept
            get the new values and call callback with those values'''
            if response == gui.stock.ACCEPT:
                use_http = http_chk.isChecked()
                use_ipv6 = ipv6_chk.isChecked()
                use_proxy = proxy_chk.isChecked()
                use_auth = auth_chk.isChecked()
                proxy_host = str(proxy_host_edit.text())
                proxy_port = str(proxy_port_edit.text())
                server_host = str(server_host_edit.text())
                server_port = str(server_port_edit.text())
                user = str(user_edit.text())
                passwd = str(pwd_edit.text())

                service = str(session_cmb.currentText())
                session_id, ext = name_to_ext[service]
                log.debug(str(session_id))
                callback(use_http, use_ipv6, use_proxy, proxy_host, proxy_port,
                         use_auth, user, passwd, session_id, service,
                         server_host, server_port)
            dialog.hide()

        dialog           = OkCancelDialog(unicode(tr('Connection preferences')))
        session_lbl      = QtGui.QLabel(unicode(tr('Session:')))
        session_cmb      = QtGui.QComboBox()
        server_host_lbl  = QtGui.QLabel(unicode(tr('Server')))
        server_host_edit = QtGui.QLineEdit()
        server_port_lbl  = QtGui.QLabel(unicode(tr('Port')))
        server_port_edit = QtGui.QLineEdit()
        http_chk         = QtGui.QCheckBox(unicode(tr('Use HTTP method')))
        proxy_chk        = QtGui.QCheckBox(unicode(tr('Use proxy')))
        host_lbl         = QtGui.QLabel(unicode(tr('Host')))
        proxy_host_edit  = QtGui.QLineEdit()
        port_lbl         = QtGui.QLabel(unicode(tr('Port')))
        proxy_port_edit  = QtGui.QLineEdit()
        auth_chk         = QtGui.QCheckBox(unicode(tr('Use authentication')))
        user_lbl         = QtGui.QLabel(unicode(tr('User')))
        user_edit        = QtGui.QLineEdit()
        pwd_lbl          = QtGui.QLabel(unicode(tr('Password')))
        pwd_edit         = QtGui.QLineEdit()

        grid_lay = QtGui.QGridLayout()
        grid_lay.setHorizontalSpacing(20)
        grid_lay.setVerticalSpacing(4)
        grid_lay.addWidget(session_lbl, 0, 0)
        grid_lay.addWidget(session_cmb, 0, 2)
        grid_lay.addWidget(server_host_lbl, 1, 0)
        grid_lay.addWidget(server_host_edit, 1, 2)
        grid_lay.addWidget(server_port_lbl, 2, 0)
        grid_lay.addWidget(server_port_edit, 2, 2)
        grid_lay.addWidget(http_chk, 3, 0, 1, -1)
        grid_lay.addWidget(proxy_chk, 4, 0, 1, -1)
        grid_lay.addWidget(host_lbl, 5, 0)
        grid_lay.addWidget(proxy_host_edit, 5, 2)
        grid_lay.addWidget(port_lbl, 6, 0)
        grid_lay.addWidget(proxy_port_edit, 6, 2)
        grid_lay.addWidget(auth_chk, 7, 0, 1, -1)
        grid_lay.addWidget(user_lbl, 8, 0)
        grid_lay.addWidget(user_edit, 8, 2)
        grid_lay.addWidget(pwd_lbl, 9, 0)
        grid_lay.addWidget(pwd_edit, 9, 2)
        dialog.setLayout(grid_lay)

        dialog.setWindowTitle(tr('Preferences'))
        server_host_edit.setText(service_host)
        server_port_edit.setText(service_port)
        proxy_host_edit.setText(proxy.host or '')
        proxy_port_edit.setText(proxy.port or '')
        user_edit.setText(proxy.user or '')
        pwd_edit.setText(proxy.passwd or '')
        #pwd_edit.setVisible(False)
        http_chk.setChecked(use_http)
        http_chk.setChecked(use_ipv6)

        index = 0
        count = 0
        name_to_ext = {}
        session_found = False
        default_session_index = 0
        default_session = extension.get_default('session')
        for ext_id, ext in extension.get_extensions('session').iteritems():
            if default_session.NAME == ext.NAME:
                default_session_index = count
            for service_name, service_data in ext.SERVICES.iteritems():
                if service == service_name:
                    index = count
                    server_host_edit.setText(service_data['host'])
                    server_port_edit.setText(service_data['port'])
                    session_found = True
                session_cmb.addItem(service_name)
                name_to_ext[service_name] = (ext_id, ext)
                count += 1
        if session_found:
            session_cmb.setCurrentIndex(index)
        else:
            session_cmb.setCurrentIndex(default_session_index)

        session_cmb.currentIndexChanged.connect(on_session_changed)
        proxy_chk.toggled.connect(on_use_proxy_toggled)
        auth_chk.toggled.connect(lambda checked:
                                 on_use_auth_toggled(auth_chk.isEnabled(), checked))

        # putting these there to trigger the slots:
        proxy_chk.setChecked(not proxy.use_proxy)
        proxy_chk.setChecked(proxy.use_proxy)
        auth_chk.setChecked(not proxy.use_auth)
        auth_chk.setChecked(proxy.use_auth)

        dialog.resize(300, 300)
        dialog.show()

        #for widget in proxy_settings:
            #widget.hide()

        response = dialog.exec_()

        if response == QtGui.QDialog.Accepted:
            response = gui.stock.ACCEPT
        elif response == QtGui.QDialog.Rejected:
            response = gui.stock.CANCEL
        log.debug(str(response))

        response_cb(response)

    @classmethod
    def set_contact_alias(cls, account, alias, response_cb,
                          title=tr('Set alias')):
        '''show a dialog showing the current alias and asking for the new
        one, the response callback receives,  the response
        (stock.ACCEPT, stock.CANCEL, stock.CLEAR <- to remove the alias
        or stock.CLOSE), the account, the old and the new alias.
        cb args: response, account, old_alias, new_alias'''
        def _on_reset():
            dialog.done(gui.stock.CLEAR)

        dialog = EntryDialog(label=tr('New alias:'), text=alias, title=title)
        reset_btn = dialog.add_button(QtGui.QDialogButtonBox.Reset)
        reset_btn.clicked.connect(_on_reset)

        response = dialog.exec_()
        response_cb(response, account, alias, dialog.text())

    @classmethod
    def yes_no(cls, message, response_cb, *args):
        '''show a confirm dialog displaying a question and two buttons:
        Yes and No, return the response as stock.YES or stock.NO or
        stock.CLOSE if the user closes the window'''
        dialog  = YesNoDialog('')
        icon    = QtGui.QLabel()
        message = QtGui.QLabel(unicode(message))

        lay = QtGui.QHBoxLayout()
        lay.addWidget(icon)
        lay.addWidget(message)
        dialog.setLayout(lay)

        icon.setPixmap(QtGui.QIcon.fromTheme('dialog-warning').pixmap(64, 64))

        response = dialog.exec_()

        response_cb(response, *args)

    @classmethod
    def select_font(cls, style, callback):
        '''select font and if available size and style, receives a
        e3.Message.Style object with the current style
        the callback receives a new style object with the new selection
        '''
        new_qt_font, result = QtGui.QFontDialog.getFont()
        if result:
            estyle = Utils.qfont_to_style(new_qt_font, style.color)
            callback(estyle)

    @classmethod
    def select_emote(cls, session, theme, callback, max_width=16):
        '''select an emoticon, receives a gui.Theme object with the theme
        settings the callback receives the response and a string representing
        the selected emoticon
        '''
        smiley_chooser_cls = extension.get_default('smiley chooser')
        smiley_chooser = smiley_chooser_cls()
        smiley_chooser.emoticon_selected.connect(callback)
        smiley_chooser.show()

    @classmethod
    def select_color(cls, color, callback):
        '''select color, receives a e3.Message.Color with the current
        color the callback receives a new color object woth the new selection
        '''
        qt_color = Utils.e3_color_to_qcolor(color)
        new_qt_color = QtGui.QColorDialog.getColor(qt_color)
        if new_qt_color.isValid() and not new_qt_color == qt_color:
            color = Utils.qcolor_to_e3_color(new_qt_color)
            callback(color)

class StandardButtonDialog (QtGui.QDialog):
    '''Skeleton for a dialog window with standard buttons'''
    def __init__(self, title, expanding=False, parent=None):
        '''Constructor'''

        QtGui.QDialog.__init__(self, parent)

        self.central_widget = QtGui.QWidget()
        self.button_box  = QtGui.QDialogButtonBox()

        vlay = QtGui.QVBoxLayout()
        vlay.addWidget(self.central_widget)
        vlay.addSpacing(10)
        vlay.addWidget(self.button_box)
        if not expanding:
            vlay.addStretch()
        QtGui.QDialog.setLayout(self, vlay)

        self.setWindowTitle(title)

        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self._on_reject)

    def add_button(self, button):
        return self.button_box.addButton(button)

    def add_button_by_text_and_role(self, text, role):
        print '*'
        r = self.button_box.addButton(text, role)
        print '*'
        return r

    def _on_accept(self):
        '''Slot called when Ok is clicked'''
        self.done(QtGui.QDialog.Accepted)

    def _on_reject(self):
        '''Slot called when Cancel is clicked'''
        self.done(QtGui.QDialog.Rejected)

    def exec_(self):
        response = QtGui.QDialog.exec_(self)

        if response == QtGui.QDialog.Accepted:
            response = self.accept_response()
        elif response == QtGui.QDialog.Rejected:
            response = self.reject_response()

        return response

    def accept_response(self):
        raise NotImplementedError()

    def reject_response(self):
        raise NotImplementedError()

# -------------------- QT_OVERRIDE

    def setLayout(self, layout):
        '''Overrides setLayout. Sets the layout directly on
        this dialog's central widget.'''
        # pylint: disable=C0103
        self.central_widget.setLayout(layout)

class OkCancelDialog (StandardButtonDialog):
    '''Skeleton for a dialog window having Ok and Cancel buttons'''
    def __init__(self, title, expanding=False, parent=None):
        '''Constructor'''
        StandardButtonDialog.__init__(self, title, expanding, parent)

        self.add_button(QtGui.QDialogButtonBox.Cancel)
        self.add_button(QtGui.QDialogButtonBox.Ok)
        self._accept_response = gui.stock.ACCEPT
        self._reject_response = gui.stock.CANCEL

    def accept_response(self):
        return self._accept_response

    def set_accept_response(self, response):
        self._accept_response = response

    def reject_response(self):
        return self._reject_response

    def set_reject_response(self, response):
        self._reject_response = response

class YesNoDialog (StandardButtonDialog):
    '''Skeleton for a dialog window having Ok and Cancel buttons'''
    def __init__(self, title, expanding=False, parent=None):
        '''Constructor'''
        StandardButtonDialog.__init__(self, title, expanding, parent)

        self.add_button(QtGui.QDialogButtonBox.No)
        self.add_button(QtGui.QDialogButtonBox.Yes)
        self._accept_response = gui.stock.YES
        self._reject_response = gui.stock.NO

    def accept_response(self):
        return self._accept_response

    def set_accept_response(self, response):
        self._accept_response = response

    def reject_response(self):
        return self._reject_response

    def set_reject_response(self, response):
        self._reject_response = response

class ContactAddedYouDialog (QtCore.QObject):
    '''Dialog window asking wether to add to the contact list
    a contact which has just added you'''

    class Page(QtGui.QDialog):
        '''This is the actual dialog window'''
        AddRole   = QtGui.QDialog.Accepted
        DontRole  = QtGui.QDialog.Accepted + 1
        LaterRole = QtGui.QDialog.Rejected

        def __init__(self, mail, nick, title, parent=None):
            QtGui.QDialog.__init__(self, parent)

            text_lbl = QtGui.QLabel()
            icon_lbl = QtGui.QLabel()
            button_box = QtGui.QDialogButtonBox()

            hlay = QtGui.QHBoxLayout()
            hlay.addWidget(icon_lbl)
            hlay.addWidget(text_lbl)
            lay = QtGui.QVBoxLayout()
            lay.addLayout(hlay)
            lay.addSpacing(10)
            lay.addWidget(button_box)
            lay.addStretch()
            QtGui.QDialog.setLayout(self, lay)

            icon = QtGui.QIcon.fromTheme('dialog-information')
            if nick != mail:
                text = '<b>%s</b>\n<b>(%s)</b>' % (nick, mail)
            else:
                text = '<b>%s</b>' % mail
            text += tr(' has added you.\nDo you want to add '
                       'him/her to your contact list?')
            text = text.replace('\n', '<br />')

            txt = tr('Remind me later')
            add_btn   = button_box.addButton(tr('Yes'), QtGui.QDialogButtonBox.AcceptRole)
            dont_btn  = button_box.addButton(tr('No'), QtGui.QDialogButtonBox.RejectRole)
            later_btn = button_box.addButton(txt, QtGui.QDialogButtonBox.ResetRole)

            self.setWindowTitle(title)
            icon_lbl.setPixmap(icon.pixmap(64, 64))
            text_lbl.setText(text)

            add_btn.clicked.connect(lambda *args: self.done(self.AddRole))
            dont_btn.clicked.connect(lambda *args: self.done(self.DontRole))
            later_btn.clicked.connect(lambda *args: self.done(self.LaterRole))


        def exec_(self):
            log.debug('Don\'t call \'exec_\' on a Page')
            return None

    def __init__(self, accounts, done_cb, title, expanding=False, parent=None):
        '''Constructor'''
        QtCore.QObject.__init__(self, parent)

        self._done_cb  = done_cb
        self._accounts = accounts
        self._dialogs  = {}
        self._results  = {'accepted': [],
                        'rejected': []}
        i = 0
        for account in accounts:
            mail, nick = account
            page = self.Page(mail, nick, title)
            self._dialogs[mail] = page
            page.finished.connect(self._create_slot(mail))

            page.show()
            pos = page.pos()
            x = pos.x()
            y = pos.y()
            page.move(x + i * 40, y + i * 40)
            i += 1

    def _create_slot(self, mail):
        return lambda result: self._on_finished(mail, result)

    def _on_finished(self, mail, result):
        if   result == self.Page.AddRole:
            self._results['accepted'].append(mail)
        elif result == self.Page.DontRole:
            self._results['rejected'].append(mail)
        elif result != self.Page.LaterRole:
            raise TypeError('Dialog returned wrong result code: %s' %
                            result)
        del self._dialogs[mail]
        if len(self._dialogs) == 0:
            self._done_cb(self._results)

    def __del__(self):
        log.debug('ContactAddedYouDialog destroyed')

class EntryDialog (OkCancelDialog):
    '''Dialog window with a text entry.'''
    def __init__(self, label, text, title, expanding=True, parent=None):
        OkCancelDialog.__init__(self, title, expanding, parent)

        label = QtGui.QLabel(label)
        self.edit = QtGui.QLineEdit(text)

        lay = QtGui.QHBoxLayout()
        lay.addWidget(label, 100)
        lay.addWidget(self.edit)
        self.setLayout(lay)

    def text(self):
        return unicode(self.edit.text())
