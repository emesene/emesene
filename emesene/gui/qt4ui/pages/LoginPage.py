# -*- coding: utf-8 -*-

''' This module contains classes to represent the login page '''

import logging

from PyQt4          import QtGui
from PyQt4          import QtCore
from PyQt4.QtCore   import Qt

from gui.qt4ui.Utils import tr

import base64

import extension
import e3
import gui


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
                 config_dir=None, config_path=None, proxy=None, use_http=None,
                 session_id=None, cancel_clicked=False, no_autologin=False,
                 parent=None):
        '''Constructor'''
        # pylint: disable=R0913
        
        # NOTE: a 'session' is an object like e3.jabber.Session.Session, so, representing a protocol
        # a 'service' is a service using a given protocol.
         
        # instance variables:
        QtGui.QWidget.__init__(self, parent)
        gui.LoginBase.__init__(self, callback, on_preferences_changed,
                                config, config_dir, config_path,
                                proxy, use_http, session_id, no_autologin)

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
        avatar_cls          = extension.get_default('avatar')
        status_combo_cls    = extension.get_default('status combo') 
        widget_d['display_pic'] = avatar_cls(default_pic=gui.theme.image_theme.logo,
                                                clickable=False)
        widget_d['account_combo'] = QtGui.QComboBox()
        widget_d['password_edit'] = QtGui.QLineEdit()
        widget_d['status_combo']  = status_combo_cls()
        widget_d['save_account_chk'] =    \
                QtGui.QCheckBox(tr('Remember me'))
        widget_d['save_password_chk'] =   \
                QtGui.QCheckBox(tr('Remember password'))
        widget_d['auto_login_chk'] =  \
                QtGui.QCheckBox(tr('Auto-login'))
        widget_d['advanced_btn']  = QtGui.QToolButton() 
        widget_d['login_btn'] = QtGui.QPushButton(tr('Connect'))

        lay = QtGui.QVBoxLayout()
        lay.addSpacing(40)
        lay.addWidget(widget_d['display_pic'], 0, Qt.AlignCenter)
        lay.addSpacing(40)
        lay.addWidget(widget_d['account_combo'])
        lay.addWidget(widget_d['password_edit'])
        lay.addWidget(widget_d['status_combo'])
        lay.addSpacing(20)
        lay.addWidget(widget_d['save_account_chk'])
        lay.addWidget(widget_d['save_password_chk'])
        lay.addWidget(widget_d['auto_login_chk'])
        lay.addWidget(widget_d['advanced_btn'], 0, Qt.AlignRight)
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
                                  self._account_list.index(account) )

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
        widget_d['login_btn'].clicked.connect(
                                    self._on_start_login)
                                        
        self.installEventFilter(self)

        account_combo = widget_d['account_combo']
        account_combo.setMinimumWidth(220)
        account_combo.setEditable(1)
        account_combo.setDuplicatesEnabled(False) #not working... why?
        account_combo.setInsertPolicy(QtGui.QComboBox.NoInsert)
        # TODO: Investigate completion
        widget_d['password_edit'].setEchoMode(QtGui.QLineEdit.Password)
        widget_d['advanced_btn'].setAutoRaise(True)
        widget_d['advanced_btn'].setIcon(
                                    QtGui.QIcon.fromTheme('preferences-other'))
        login_btn = widget_d['login_btn']
        login_btn.setAutoDefault(True)
        login_btn.setEnabled(False)
        login_btn.setMinimumWidth(110)
                                        
    def _setup_accounts(self):
        '''Builds up the account list'''
        class Account(object):
            '''Convenience class to store account's settings'''
            def __init__(self, service, email, password, status, remember_lvl):
                '''Constructor'''
                self.service, self.status             = service, status
                self.email, self.password             = email, password
                self.save_account, self.save_password = False, False
                self.auto_login                       = False
                if remember_lvl >= 1:
                    self.save_account   = True
                if remember_lvl >= 2:
                    self.save_password  = True
                if remember_lvl >= 3:
                    self.auto_login     = True
        
        emails            = self.remembers.keys()
        default_acc_email = self.config.last_logged_account

        if default_acc_email in emails:
            index = emails.index(default_acc_email)
            # put the default account's email in the first position
            emails[0], emails[index] = emails[index], emails[0]
            
        for email in emails:
            acc = email.rpartition('|')[0]
            service = self.config.d_user_service.get(
                            email.rpartition('|')[0], 'msn')
            remember_lvl = self.remembers[email]
            if remember_lvl >= 1: # we have at least a status
                status = self.config.d_status[email]
            else:
                status = e3.status.ONLINE
            if remember_lvl >= 2: # we have also a password
                password = base64.b64decode(self.accounts[email])
            else:
                password = ''

            account = Account(service, acc, password, status, remember_lvl)
            self._account_list.append(account)


    def _on_account_combo_text_changed(self, new_text): #new text is a QString
        ''' Slot executed when the text in the account combo changes '''
        log.info('*** _on_account_combo_text_changed')
        index = self._widget_d['account_combo'].findText(new_text)
        if index > -1:
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
            # status:
            widget_d['status_combo'].set_status(account.status)
            # checkboxes:
            widget_d['save_account_chk'] .setChecked(account.save_account)
            widget_d['save_password_chk'].setChecked(account.save_password)
            widget_d['auto_login_chk']   .setChecked(account.auto_login)

            self.update_service(account.service)
        self._on_checkbox_state_refresh()
        
    def _on_connection_preferences_clicked(self):
        '''Callback invoked when the user clicks the connection preferences
        button'''
        def new_preferences_cb(use_http, use_proxy, proxy_host, proxy_port,
                               use_auth, user, passwd, session_id, service, 
                               server_host, server_port):
            '''called when the user press accept on the preferences dialog'''
            
            self.proxy = e3.Proxy(use_proxy, proxy_host,
                                   proxy_port, use_auth, user, passwd)
            self.server_host = server_host
            self.server_port = server_port
            account_email = str(self._widget_d['account_combo'].currentText())
            if account_email != '':
                self.config.d_user_service[account_email] = service
                # to trigger eventual update of dp:
            self._on_account_combo_text_changed(account_email)
            self.on_preferences_changed(use_http, self.proxy, session_id,
                    service)
            

        service = self.config.service
        account = str(self._widget_d['account_combo'].currentText())
        if account in self.config.d_user_service.keys():
            service = self.config.d_user_service[account]
        extension.get_default('dialog').login_preferences(service, self.server_host,
                                        self.server_port, new_preferences_cb, 
                                        self.config.b_use_http, self.proxy)

    def _on_start_login(self):
        ''' Slot executed when the user clicks the login button'''
        widget_dic = self._widget_d
        user = str(widget_dic['account_combo'].currentText())
        password = str(widget_dic['password_edit'].text())
        status = widget_dic['status_combo'].status()
        save_account = widget_dic['save_account_chk'].isChecked()
        save_password = widget_dic['save_password_chk'].isChecked()
        auto_login = widget_dic['auto_login_chk'].isChecked()
        
        if user in self.config.d_user_service.keys():
            service_name = self.config.d_user_service[user]
            self.session_id = self.service2id[service_name][0]
        else:
            service_name = self.config.service
            self.session_id = self.config.session
        self.config.d_user_service[user] = service_name
        
        e3_account = e3.Account(user, password, status, self.server_host)

        self.config_account(e3_account, service_name, save_account, save_password,
                            auto_login)
            
        # Invoke the  login callback
        self.callback(e3_account, self.session_id, self.proxy,
                             self.use_http, self.server_host, self.server_port)

    def clear_login_form(self, clear_pic=False):
        ''' Resets the login form '''
        log.info('*** clear_login_form')
        widget_dic = self._widget_d
        if clear_pic:
            widget_dic['display_pic'].set_default_pic()
        widget_dic['password_edit'].clear()
        widget_dic['status_combo'].set_status(e3.status.ONLINE)
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
