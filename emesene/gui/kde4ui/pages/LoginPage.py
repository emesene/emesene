# -*- coding: utf-8 -*-

''' This module contains classes to represent the login page '''

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import base64

import e3

import gui.kde4ui.widgets as Widgets


class LoginPage(QtGui.QWidget):
    ''' The Login Page '''
    # pylint: disable=W0612
    NAME = 'LoginPage'
    DESCRIPTION = 'The widget used to to dislay the login screen'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    def __init__(self, callback, on_preferences_changed, config=None,
                 config_dir=None, config_path=None, proxy=None, use_http=None,
                 session_id=None, cancel_clicked=False, parent=None):
        '''Constructor'''
        # pylint: disable=R0913
        # instance variables:
        QtGui.QWidget.__init__(self, parent)
        self._account_list = []

        self._config = config
        self._config_dir = config_dir
        self._config_path = config_path
        self._session_id = session_id
        self._proxy = proxy
        self._use_http = use_http
        self._login_callback = callback

        # a widget dic to avoid proliferation of instance variables:
        self._widget_dict = {}

        # setup code:
        self._setup_accounts()
        self._setup_ui()
        
        # selects the default account if any:
        account_combo = self._widget_dict['account_combo']
        if self._config.last_logged_account and \
           not self._config.last_logged_account == '':
            account_combo.setCurrentIndex(account_combo.findData(0))
        # I don't know why this doesn't get called automatically:
        self._on_chosen_account_changed(0)   
            
        # TODO: this way, if there are remembered accounts, but no default 
        #account, no display pic is shown....
        

    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dict
        widget_dict['display_pic'] = Widgets.DisplayPic(self._config_dir,
                                                    'messenger.hotmail.com')
        widget_dict['account_combo'] = KdeGui.KComboBox()
        widget_dict['password_edit'] = KdeGui.KLineEdit()
        widget_dict['status_combo'] = Widgets.StatusCombo()
        widget_dict['save_account_chk'] =    \
                QtGui.QCheckBox(i18n("Remember this account"))
        widget_dict['save_password_chk'] =   \
                QtGui.QCheckBox(i18n("Save password"))
        widget_dict['auto_login_chk'] =  \
                QtGui.QCheckBox(i18n("Login automagically"))
        widget_dict['login_btn'] = KdeGui.KPushButton(i18n("Login"))

        lay = QtGui.QVBoxLayout()
        lay.addSpacing(40)
        lay.addWidget(widget_dict['display_pic'], 0, Qt.AlignCenter)
        lay.addSpacing(40)
        lay.addWidget(widget_dict['account_combo'])
        lay.addWidget(widget_dict['password_edit'])
        lay.addWidget(widget_dict['status_combo'])
        lay.addSpacing(20)
        lay.addWidget(widget_dict['save_account_chk'])
        lay.addWidget(widget_dict['save_password_chk'])
        lay.addWidget(widget_dict['auto_login_chk'])
        lay.addSpacing(35)
        lay.addWidget(widget_dict['login_btn'], 0, Qt.AlignCenter)
        lay.addSpacing(45)
        lay.addStretch()

        hor_lay = QtGui.QHBoxLayout()
        hor_lay.addStretch()
        hor_lay.addSpacing(40)
        hor_lay.addLayout(lay)
        hor_lay.addSpacing(40)
        hor_lay.addStretch()
        self.setLayout(hor_lay)
        
        # insert accounts in the combo box:
        account_combo = widget_dict['account_combo']
        for account in self._account_list:
            account_combo.addItem(account.email,
                                  self._account_list.index(account) )

        widget_dict['account_combo'].currentIndexChanged.connect(
                                        self._on_chosen_account_changed)
        widget_dict['account_combo'].editTextChanged.connect(
                                        self._on_account_combo_text_changed)
        widget_dict['password_edit'].textChanged.connect(
                                        self._on_checkbox_state_refresh)
        widget_dict['save_account_chk'].stateChanged.connect(
                                        self._on_checkbox_state_refresh)
        widget_dict['save_password_chk'].stateChanged.connect(
                                        self._on_checkbox_state_refresh) 
        widget_dict['auto_login_chk'].stateChanged.connect(
                                        self._on_checkbox_state_refresh)
        widget_dict['login_btn'].clicked.connect(
                                        self._on_start_login)
                                        
        self.installEventFilter(self)

        widget_dict['display_pic'].set_clickable(False)
        account_combo = widget_dict['account_combo']
        account_combo.setMinimumWidth(220)
        account_combo.setEditable(1)
        account_combo.setDuplicatesEnabled(False) #not working... why?
        account_combo.setInsertPolicy(KdeGui.KComboBox.NoInsert)
        # TODO: Investigate completion
        widget_dict['password_edit'].setPasswordMode()
        login_btn = widget_dict['login_btn']
        login_btn.setAutoDefault(True)
        login_btn.setEnabled(False)
        login_btn.setMinimumWidth(110)
                                        



    def _setup_accounts(self):
        '''Builds up the account list'''
        class Account(object):
            '''Convenience class to store account's settings'''
            def __init__(self, email, password, status, remember_level):
                '''Constructor'''
                self.email, self.password             = email, password
                self.status                           = status
                self.save_account, self.save_password = False, False
                self.auto_login                       = False
                if remember_level >= 1:
                    self.save_account   = True
                if remember_level >= 2:
                    self.save_password  = True
                if remember_level >= 3:
                    self.auto_login     = True
        
        remember_level_dict = self._config.d_remembers
        emails = remember_level_dict.keys()
        status_dict = self._config.d_status
        password_dict = self._config.d_accounts
        email_of_default_account = self._config.last_logged_account

        if email_of_default_account in emails:
            index = emails.index(email_of_default_account)
            # put the default account's email in the first position
            emails[0], emails[index] = emails[index], emails[0]
            
        for email in emails:
            remember_level = remember_level_dict[email]
            if remember_level >= 1: # we have at least a status
                status = status_dict[email]
            else:
                status = e3.status.ONLINE
            if remember_level >= 2: # we have also a password
                password = base64.b64decode(password_dict[email])
            else:
                password = ''

            account = Account(email, password, status, remember_level)
            self._account_list.append(account)



    def _on_account_combo_text_changed(self, new_text): #new text is a QString
        ''' Slot executed when the text in the account combo changes '''
        print " *** _on_account_combo_text_changed"
        index = self._widget_dict['account_combo'].findText(new_text)
        if index > -1:
            self._on_chosen_account_changed(index)
        else:
            self.clear_login_form(clear_pic=True)
        self._on_checkbox_state_refresh()


    def _on_chosen_account_changed(self, acc_index):
        ''' Slot executed when the user select another account from the drop
        down menu of the account combo'''
        print " *** _on_chosen_account_changed"
        widget_dict = self._widget_dict
        account_combo  = widget_dict['account_combo']
        password_edit  = widget_dict['password_edit']
        index_in_account_list = account_combo.itemData(acc_index).toPyObject()
        account = self._account_list[index_in_account_list]
        
        self.clear_login_form()
        # display_pic
        widget_dict['display_pic'].set_display_pic(account.email)
        # password:
        if account.password:
            password_edit.setText(account.password)
        else:
            password_edit.clear()
        # status:
        widget_dict['status_combo'].set_status(account.status)
        # checkboxes:
        widget_dict['save_account_chk'] .setChecked(account.save_account)
        widget_dict['save_password_chk'].setChecked(account.save_password)
        widget_dict['auto_login_chk']   .setChecked(account.auto_login)
        self._on_checkbox_state_refresh()


    def _on_start_login(self):
        ''' Slot executed when the user clicks the login button'''
        widget_dic = self._widget_dict
        user            =  str(widget_dic['account_combo'].currentText())
        password        =  str(widget_dic['password_edit'].text())
        status          =      widget_dic['status_combo'].status()
        save_account    =      widget_dic['save_account_chk'].isChecked()
        save_password   =      widget_dic['save_password_chk'].isChecked()
        auto_login      =      widget_dic['auto_login_chk'].isChecked()

        e3_account = e3.Account(user, password, status, 'messenger.hotmail.com')
        #is this the email?
        email = e3_account.account


        # saves the account's config:
        # the "remember field behaves like this:
        # - 0: save nothing                 - 1: save account
        # - 2: save account and password    - 3: save all and autologin
        
        
        # TODO: when there's no config file, we have already a d_remembers and 
        # a d_accounts, but no d_status and last_logged_account. This seems to
        # be inconsistent. Is this a bug?
        d_remembers = self._config.d_remembers
        d_accounts = self._config.d_accounts
        d_status = self._config.d_status
        if not d_status:
            self._config.get_or_set('d_status', {})
            d_status = self._config.d_status
        if not self._config.last_logged_account:
            self._config.get_or_set('last_logged_account', '')
            
        
        
        if save_account:
            d_remembers[email] = 1
            d_status[email] = status
            self._config.last_logged_account = email
            if save_password:
                d_remembers[email] = 2
                d_accounts[email] = base64.b64encode(e3_account.password)
                if auto_login:
                    d_remembers[email] = 3
            else:
                if  email in d_accounts:
                    del d_accounts[email]
        else:
            if email in d_remembers:
                del d_remembers[email]
            if email in d_status:
                del d_status[email]
            if email in d_accounts:
                del d_accounts[email]
         
         # alternative form: 
#        if auto_login:
#            self._config.last_logged_account = email
#            d_remembers[email] = 3
#            d_status[email] = status
#            d_accounts[email] = base64.b64encode(e3_account.password)
#        elif save_password:
#            d_remembers[email] = 2
#            self._config.last_logged_account = email
#            d_status[email] = status
#            d_accounts[email] = base64.b64encode(e3_account.password)
#        elif save_account:
#            self._config.last_logged_account = email
#            d_remembers[email] = 1
#            d_status[email] = status
#            if  email in d_accounts:
#                del d_accounts[email]
#        else:
#            if email in d_remembers:
#                del d_remembers[email]
#            if email in d_status:
#                del d_status[email]
#            if  email in d_accounts:
#                del d_accounts[email]
            
                
        self._config.save(self._config_path)
            
        # Invoke the  login callback
        self._login_callback(e3_account, self._session_id, self._proxy,
                             self._use_http, 'omega.contacts.msn.com', '1863')



    def clear_login_form(self, clear_pic=False):
        ''' Resets the login form '''
        print " *** clear_login_form"
        widget_dic = self._widget_dict
        if clear_pic:
            widget_dic['display_pic'].set_logo()
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
        #print " *** _widget_status_refresh"
        widget_dict = self._widget_dict
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
            self._widget_dict['login_btn'].animateClick()
            return True
        else:
            return False
            
        
