# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
''' This module contains classes to represent the login page '''

import logging

from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from gui.qt4ui.Utils import tr

import extension
import e3
import gui
from gui.qt4ui.widgets import StatusButton

log = logging.getLogger('qt4ui.LoginPage')

class LoginPage(QtGui.QWidget, gui.LoginBase):
    ''' The Login Page '''
    # pylint: disable=W0612
    NAME = 'LoginPage'
    DESCRIPTION = 'The widget used to to dislay the login screen'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, callback, on_preferences_changed, config=None,
                 config_dir=None, config_path=None, proxy=None, use_http=None, use_ipv6=None,
                 session_id=None, cancel_clicked=False, no_autologin=False,
                 parent=None):
        '''Constructor'''
        # pylint: disable=R0913
        QtGui.QWidget.__init__(self, parent)
        gui.LoginBase.__init__(self, callback, on_preferences_changed,
                                config, config_dir, config_path,
                                proxy, use_http, use_ipv6, session_id, no_autologin)

        # a widget dic to avoid proliferation of instance variables:
        self._widget_d = {}
        self._account_list = []
        self.autologin_started = False

        # setup code:
        self._setup_accounts()
        self._setup_ui()
        self._on_chosen_account_changed(0)

        # selects the default account if any:
        account_combo = self._widget_d['account_combo']

        if self.config.last_logged_account != '':
            account_combo.setCurrentIndex(account_combo.findData(0))
            self._on_chosen_account_changed(0)
            if not cancel_clicked and not self.no_autologin and \
                    config.d_remembers[config.last_logged_account] == 3:
                self.autologin_started = True
                self._on_start_login()

        # TODO: this way, if there are remembered accounts, but no default 
        #account, no display pic is shown....

    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_d = self._widget_d
        avatar_cls = extension.get_default('avatar')
        widget_d['display_pic'] = avatar_cls(default_pic=gui.theme.image_theme.logo,
                                            clickable=False)
        account_box = QtGui.QHBoxLayout()
        widget_d['account_box'] = account_box
        widget_d['account_combo'] = QtGui.QComboBox()
        account_img = QtGui.QLabel()
        account_img.setPixmap(QtGui.QPixmap(gui.theme.image_theme.user))
        widget_d['account_img'] = account_img
        widget_d['forget_me_btn']  = QtGui.QToolButton()
        widget_d['forget_me_btn'].setAutoRaise(True)
        widget_d['forget_me_btn'].setIcon(
                                    QtGui.QIcon.fromTheme('edit-delete'))
        account_box.addWidget(widget_d['account_img'])
        account_box.addWidget(widget_d['account_combo'])
        account_box.addWidget(widget_d['forget_me_btn'])

        password_box = QtGui.QHBoxLayout()
        widget_d['password_box'] = password_box
        widget_d['password_edit'] = QtGui.QLineEdit()
        # TODO: Investigate completion
        widget_d['password_edit'].setEchoMode(QtGui.QLineEdit.Password)
        password_img = QtGui.QLabel()
        password_img.setPixmap(QtGui.QPixmap(gui.theme.image_theme.password))
        widget_d['password_img'] = password_img
        password_box.addWidget(widget_d['password_img'])
        password_box.addWidget(widget_d['password_edit'])

        widget_d['status_btn'] = StatusButton.StatusButton()
        widget_d['status_btn'].setToolTip(_('Status'))
        widget_d['status_btn'].set_status(e3.status.ONLINE)
        password_box.addWidget(widget_d['status_btn'])

        service_box = QtGui.QHBoxLayout()
        widget_d['service_box'] = service_box
        widget_d['service_combo'] = QtGui.QComboBox()
        widget_d['service_combo'].setMinimumWidth(220)
        service_img = QtGui.QLabel()
        service_img.setPixmap(QtGui.QPixmap(gui.theme.image_theme.connect))
        widget_d['service_img'] = service_img
        widget_d['advanced_btn'] = QtGui.QToolButton()
        widget_d['advanced_btn'].setAutoRaise(True)
        widget_d['advanced_btn'].setIcon(
                                    QtGui.QIcon.fromTheme('preferences-other'))
        service_box.addWidget(widget_d['service_img'])
        service_box.addWidget(widget_d['service_combo'])
        service_box.addWidget(widget_d['advanced_btn'])

        layv = QtGui.QVBoxLayout()
        widget_d['save_account_chk'] =    \
                QtGui.QCheckBox(tr('Remember me'))
        widget_d['save_password_chk'] =   \
                QtGui.QCheckBox(tr('Remember password'))
        widget_d['auto_login_chk'] =  \
                QtGui.QCheckBox(tr('Auto-login'))
        widget_d['login_btn'] = QtGui.QPushButton(tr('Connect'))

        lay = QtGui.QVBoxLayout()
        lay.setContentsMargins (0,0,0,0)
        lay.addSpacing(40)
        lay.addWidget(widget_d['display_pic'], 0, Qt.AlignCenter)
        lay.addSpacing(40)
        lay.addLayout(widget_d['account_box'])
        lay.addLayout(widget_d['password_box'])
        lay.addLayout(widget_d['service_box'])
        lay.addSpacing(20)
        lay.addWidget(widget_d['save_account_chk'])
        lay.addWidget(widget_d['save_password_chk'])
        lay.addWidget(widget_d['auto_login_chk'])
        lay.addSpacing(35)
        lay.addStretch()
        lay.addWidget(widget_d['login_btn'], 0, Qt.AlignCenter)
        lay.addSpacing(45)

        hor_lay = QtGui.QHBoxLayout()
        hor_lay.addStretch()
        hor_lay.addSpacing(40)
        hor_lay.addLayout(lay)
        hor_lay.addSpacing(40)
        hor_lay.addStretch()
        self.setLayout(hor_lay)

        # insert accounts in the combo box:
        account_combo = widget_d['account_combo']
        for account in self._account_list:
            account_combo.addItem(account.email,
                                  self._account_list.index(account))

        widget_d['account_combo'].currentIndexChanged.connect(
                                    self._on_chosen_account_changed)
        widget_d['account_combo'].editTextChanged.connect(
                                    self._on_account_combo_text_changed)
        widget_d['password_edit'].textChanged.connect(
                                    self._on_checkbox_state_refresh)
        widget_d['save_account_chk'].stateChanged.connect(
                                    self._on_checkbox_state_refresh)
        widget_d['save_password_chk'].stateChanged.connect(
                                    self._on_checkbox_state_refresh)
        widget_d['auto_login_chk'].stateChanged.connect(
                                    self._on_checkbox_state_refresh)
        widget_d['advanced_btn'].clicked.connect(
                                    self._on_connection_preferences_clicked)
        widget_d['forget_me_btn'].clicked.connect(
                                    self._on_forget_me_clicked)
        widget_d['login_btn'].clicked.connect(
                                    self._on_start_login)
        self.installEventFilter(self)

        account_combo = widget_d['account_combo']
        account_combo.setMinimumWidth(220)
        account_combo.setEditable(1)
        account_combo.setDuplicatesEnabled(False) #not working... why?
        account_combo.setInsertPolicy(QtGui.QComboBox.NoInsert)

        login_btn = widget_d['login_btn']
        login_btn.setAutoDefault(True)
        login_btn.setEnabled(False)
        login_btn.setMinimumWidth(110)
        self.new_combo_session()

    def _setup_accounts(self):
        '''Builds up the account list'''
        emails = self.remembers.keys()
        default_acc_email = self.config.last_logged_account

        if default_acc_email in emails:
            index = emails.index(default_acc_email)
            # put the default account's email in the first position
            emails[0], emails[index] = emails[index], emails[0]

        for email in emails:
            acc = email.rpartition('|')[0]
            service = self.config.d_user_service.get(acc, 'msn')
            remember_lvl = self.remembers[email]
            status = self.config.d_status.get(email, e3.status.ONLINE)
            password = self.decode_password(email)

            account = LoginPage.Account(service, acc, password, status, remember_lvl)
            self._account_list.append(account)

    def _on_account_combo_text_changed(self, new_text, from_preferences=False): #new text is a QString
        ''' Slot executed when the text in the account combo changes '''
        index = self._widget_d['account_combo'].findText(new_text)
        service = str(self._widget_d['service_combo'].currentText())
        if index > -1 and from_preferences and self.search_account(service, new_text):
            self._on_chosen_account_changed(index)
        else:
            self.clear_login_form(clear_pic=True)
        self._on_checkbox_state_refresh()

    def _on_chosen_account_changed(self, acc_index):
        ''' Slot executed when the user select another account from the drop
        down menu of the account combo'''
        log.info('*** _on_chosen_account_changed')
        widget_d = self._widget_d
        account_combo  = widget_d['account_combo']
        password_edit  = widget_d['password_edit']
        index_in_account_list = account_combo.itemData(acc_index).toPyObject()
        # If we don't have any account at all, this slots gets called but 
        # index_in_account_list is None.
        if not index_in_account_list is None:
            account = self._account_list[index_in_account_list]
            self.clear_login_form()
            # display_pic
            path = self.current_avatar_path(account.email)
            widget_d['display_pic'].set_display_pic_from_file(path)
            # password:
            if account.password:
                password_edit.setText(account.password)
            else:
                password_edit.clear()
            #service
            widget_d['service_combo'].setCurrentIndex(
                        self.session_name_to_index.get(account.service, 0))
            # status:
            ext = self.service2id[account.service][1]
            widget_d['status_btn'].setEnabled(ext.SERVICE_STATUS in ext.CAPABILITIES)
            widget_d['status_btn'].set_status(account.status)
            # checkboxes:
            widget_d['save_account_chk'].setChecked(account.save_account)
            widget_d['save_password_chk'].setChecked(account.save_password)
            widget_d['auto_login_chk'].setChecked(account.auto_login)

            self.update_service(account.service)
        self._on_checkbox_state_refresh()

    def search_account(self, service, email):
        for account in self._account_list:
            if account.email == email and account.service == service:
                return True
        return False

    def on_session_changed(self, index, *args):
        '''Callback called when the session type in the combo is
            called'''
        service = str(self._widget_d['service_combo'].currentText())
        session_id, ext = self.service2id[service]
        account_email = str(self._widget_d['account_combo'].currentText())
        if account_email != '':
            self.config.d_user_service[account_email] = service

        self.new_preferences_cb(
            self.use_http, self.use_ipv6, self.proxy, service,
            ext.SERVICES[service]['host'], ext.SERVICES[service]['port'])

        # to trigger eventual update of dp:
        self._on_account_combo_text_changed(account_email, True)

    def service_add_cb(self, s_name, service_name):
        '''Add a new service to the service combo'''
        if not s_name is None:
            image = QtGui.QIcon(s_name)
        else:
            image = None
        self._widget_d['service_combo'].addItem(image, service_name)

    def new_combo_session(self):
        '''populate service combo with avariable services'''
        index = gui.LoginBase.new_combo_session(self, self.service_add_cb)
        self._widget_d['service_combo'].setCurrentIndex(index)
        self._widget_d['service_combo'].currentIndexChanged.connect(self.on_session_changed)

    def new_preferences_cb(self, use_http, use_ipv6, proxy,
                            service, server_host, server_port):
        '''called when the user press accept on the preferences dialog'''
        self.session_id = self.service2id[service][0]
        self.use_http = use_http
        self.use_ipv6 = use_ipv6
        self.server_host = server_host
        self.server_port = server_port
        self.proxy = proxy
        self.on_preferences_changed(use_http, use_ipv6, self.proxy, self.session_id,
                service)

    def _on_connection_preferences_clicked(self):
        '''Callback invoked when the user clicks the connection preferences
        button'''
        account = str(self._widget_d['account_combo'].currentText())
        self._on_preferences_open(account, self.new_preferences_cb)

    def _on_forget_me_clicked(self):
        ''''''
        def _yes_no_cb(response):
            '''callback from the confirmation dialog'''
            if (response == 36): #Accepted
                account = str(widget_dic['account_combo'].currentText())
                service = self.config.d_user_service.get(account, self.config.service)
                self.forget_user(account, service)
                #FIXME: remove fron account_list and combo
                widget_dic['account_combo'].setCurrentIndex(0)

        widget_dic = self._widget_d
        extension.get_default('dialog').yes_no(
                _('Are you sure you want to delete the account %s ?') % \
                str(widget_dic['account_combo'].currentText()), _yes_no_cb)

    def _on_start_login(self):
        ''' Slot executed when the user clicks the login button'''
        widget_dic = self._widget_d
        user = str(widget_dic['account_combo'].currentText())
        password = str(widget_dic['password_edit'].text())
        status = widget_dic['status_btn'].status
        save_account = widget_dic['save_account_chk'].isChecked()
        save_password = widget_dic['save_password_chk'].isChecked()
        auto_login = widget_dic['auto_login_chk'].isChecked()
        service_name = str(self._widget_d['service_combo'].currentText())

        account = e3.Account(user, password, status, self.server_host)
        self.config_account(account, service_name, save_account, save_password,
                            auto_login)
        account.uuid = self.account_uuid
            
        # Invoke the  login callback
        self.callback(account, self.session_id, self.proxy,
                            self.use_http, self.use_ipv6, self.server_host,
                            self.server_port)

    def clear_login_form(self, clear_pic=False):
        ''' Resets the login form '''
        widget_dic = self._widget_d
        if clear_pic:
            widget_dic['display_pic'].set_default_pic()
        widget_dic['password_edit'].clear()
        widget_dic['status_btn'].set_status(e3.status.ONLINE)
        # _on_checkbox_state_changed enables them:
        widget_dic['auto_login_chk'].setChecked(False)
        widget_dic['save_password_chk'].setChecked(False)
        widget_dic['save_account_chk'].setChecked(False)
        
    
    def _on_checkbox_state_refresh(self):
        ''' Checks wether each checkbox in the login page should be
        enabled or disabled, checked or unchecked and changes its
        state accordingly'''
        widget_dict = self._widget_d
        account_combo       = widget_dict['account_combo']
        password_edit       = widget_dict['password_edit']
        save_account_chk    = widget_dict['save_account_chk']
        save_password_chk   = widget_dict['save_password_chk']
        auto_login_chk      = widget_dict['auto_login_chk']
        login_btn           = widget_dict['login_btn']
        
        if auto_login_chk.isChecked():
            save_password_chk.setChecked(True)
            save_password_chk.setEnabled(False)
        else:
            save_password_chk.setEnabled(True)
            
        if save_password_chk.isChecked():
            save_account_chk.setChecked(True)
            save_account_chk.setEnabled(False)
        else:
            save_account_chk.setEnabled(True)
            
        if (not account_combo.currentText().isEmpty()) and  \
           (not password_edit.text().isEmpty()):  
            login_btn.setEnabled(True)
        else:
            login_btn.setEnabled(False)

    def clear_all(self, clear_pic=False):
        '''
        clear all login fields and checkbox
        '''
        widget_dic = self._widget_d
        if clear_pic:
            widget_dic['display_pic'].set_default_pic()
        widget_dic['password_edit'].clear()
        widget_dic['status_btn'].set_status(e3.status.ONLINE)
        # _on_checkbox_state_changed enables them:
        widget_dic['auto_login_chk'].setChecked(False)
        widget_dic['save_password_chk'].setChecked(False)
        widget_dic['save_account_chk'].setChecked(False)

    def show_error(self, reason, login_failed=False):
        '''
        show an error on the top of the window using nicebar
        '''
        if login_failed:
            self._widget_dic['auto_login_chk'].setChecked(False)
        #FIXME: implement nicebar in qt4

    # -------------------- QT_OVERRIDE

    def eventFilter(self, obj, event):
        ''' event filter to handle return pression in the login window'''
        # pylint: disable=C0103
        if not obj == self:
            return False
        if event.type() == QtCore.QEvent.KeyRelease and \
            event.key() == Qt.Key_Return:
            self._widget_d['login_btn'].animateClick()
            return True
        else:
            return False

    class Account(object):
        '''Convenience class to store account's settings'''
        def __init__(self, service, email, password, status, remember_lvl):
            '''Constructor'''
            self.service, self.status = service, status
            self.email, self.password = email, password
            self.save_account, self.save_password = False, False
            self.auto_login = False
            if remember_lvl >= 1:
                self.save_account = True
            if remember_lvl >= 2:
                self.save_password = True
            if remember_lvl >= 3:
                self.auto_login = True
