# -*- coding: utf-8 -*-

''' This module contains classes to represent the login page '''

import PyKDE4.kdeui     as KdeGui
from PyKDE4.kdecore import i18n
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import base64

import e3

from gui.kde4ui.widgets import DisplayPic, PresenceCombo


#TODO: Consider reimplementing LoginPage as a Qt state machine
class LoginPage(QtGui.QWidget):
    ''' The Login Page '''
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
        self._is_account_valid = False
        self._is_there_a_password = False

        # a widget dic to avoid proliferation of instance variables:
        self._widget_dic = {}
        widget_dic = self._widget_dic

        # setup code:
        self._setup_accounts()
        self._setup_ui()
        self.installEventFilter(self)

        widget_dic['display_pic'].set_clickable(False)
        account_combo = widget_dic['account_combo']
        account_combo.setMinimumWidth(220)
        account_combo.setEditable(1)
        account_combo.setDuplicatesEnabled(False) #not working... why?
        account_combo.setInsertPolicy(KdeGui.KComboBox.NoInsert)
        # ?
        account_combo_completion = \
            account_combo.completionObject(True)
        password_edit = widget_dic['password_edit']
        password_edit.setPasswordMode()
        login_btn = widget_dic['login_btn']
        login_btn.setAutoDefault(True)
        login_btn.setMinimumWidth(110)


    def _setup_ui(self):
        '''Instantiates the widgets, and sets the layout'''
        widget_dict = self._widget_dic
        widget_dict['display_pic'] = DisplayPic()
        widget_dict['account_combo'] = KdeGui.KComboBox()
        widget_dict['password_edit'] = KdeGui.KLineEdit()
        widget_dict['presence_combo'] = PresenceCombo()
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
        lay.addWidget(widget_dict['presence_combo'])
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

        #TODO: Check signal propagation - loop risk!
        widget_dict['account_combo'].currentIndexChanged.connect(
                                        self._on_chosen_account_changed)
        widget_dict['account_combo'].editTextChanged.connect(
                                        self._on_account_combo_text_changed)
        widget_dict['password_edit'].textChanged.connect(
                                        self._on_password_text_changed)
        widget_dict['login_btn'].clicked.connect(
                                        self._on_start_login)

        account_combo = widget_dict['account_combo']
        for account in self._account_list:
            account_combo.addItem(account.email,
                                  self._account_list.index(account) )
        if self._config.last_logged_account and \
           not self._config.last_logged_account == '':
            account_combo.setCurrentIndex(account_combo.findData(0))



    def _setup_accounts(self):
        '''Builds up the account list'''
        class Account(object):
            def __init__(self, email, password, presence, remember_level):
                self.email, self.password             = email, password
                self.presence                         = presence
                self.save_account, self.save_password = False, False
                self.auto_login                       = False
                if remember_level >= 1:
                    self.save_account   = True
                if remember_level >= 2:
                    self.save_password  = True
                if remember_level >= 3:
                    self.auto_login     = True

        email_pwd_dict = self._config.d_accounts
        email_presence_dict = self._config.d_status
        email_remember_level_dict = self._config.d_remembers
        email_of_default_account = self._config.last_logged_account

        if email_of_default_account in email_pwd_dict.keys():
            email = email_of_default_account
            account = Account(email,
                              base64.b64decode(email_pwd_dict[email]),
                              email_presence_dict[email],
                              email_remember_level_dict[email] )
            self._account_list.append(account)

        for email in email_pwd_dict.keys():
            if email == email_of_default_account:
                continue
            account = Account(email,
                              base64.b64decode(email_pwd_dict[email]),
                              email_presence_dict[email],
                              email_remember_level_dic[email] )
            self._account_list.append(account)



    def _on_account_combo_text_changed(self, new_text): #new text is a QString
        ''' Slot executed when the text in the account combo changes '''
        print " *** _on_account_combo_text_changed"
        index = self._widget_dic['account_combo'].findText(new_text)
        if is_valid_mail(str(new_text)):
            self._is_account_valid = True
            if index > -1:
                self._on_chosen_account_changed(index)
            else:
                self.clear_login_form()
        else:
            self.clear_login_form()
            self._is_account_valid = False
        self._widget_status_refresh()


    def _on_chosen_account_changed(self, acc_index):
        ''' Slot executed when the user select another account from the drop
        down menu of the account combo'''
        print " *** _on_chosen_account_changed"
        widget_dict = self._widget_dic
        account_combo  = widget_dict['account_combo']
        password_edit  = widget_dict['password_edit']
        index_in_account_list = account_combo.itemData(acc_index).toPyObject()
        account = self._account_list[index_in_account_list]
        # email:
        self._is_account_valid = True
        # password:
        if account.password:
            password_edit.setText(account.password)
        else:
            password_edit.clear()
        # presence:
        widget_dict['presence_combo'].set_presence(account.presence)
        # checkboxes:
        widget_dict['save_account_chk'] .setChecked(account.save_account)
        widget_dict['save_password_chk'].setChecked(account.save_password)
        widget_dict['auto_login_chk']   .setChecked(account.auto_login)
        self._widget_status_refresh()


    def _on_start_login(self):
        ''' Slot executed when the user clicks the login button'''
        widget_dic = self._widget_dic
        user            =  str(widget_dic['account_combo'].currentText())
        password        =  str(widget_dic['password_edit'].text())
        status          =      widget_dic['presence_combo'].presence()
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
        self._config.d_remembers[email] = 0
        if save_account:
            self._config.d_remembers[email] = 1
            self._config.last_logged_account = email
            self._config.d_status[email] = status
        if save_password:
            self._config.d_remembers[email] = 2
            self._config.d_accounts[email] = base64.b64encode(account.password)
        if auto_login:
            self._config.d_remembers[email] = 3
        self._config.save(self._config_path)

        # Invoke the  login callback
        self._login_callback(e3_account, self._session_id, self._proxy,
                             self._use_http, 'messenger.hotmail.com', '1863')


    def _on_password_text_changed(self, pwd):
        ''' Slot executed when the password_edit is edited. Disables
        the "Save Password" checkbox if password_edit is empty'''
        print " *** _on_password_text_changed"
        if pwd.isEmpty():
            self._is_there_a_password = False
        else:
            self._is_there_a_password = True
        self._widget_status_refresh()

    def clear_login_form(self):
        ''' Resets the login form '''
        print " *** clear_login_form"
        widget_dic = self._widget_dic
        widget_dic['password_edit'].clear()
        widget_dic['presence_combo'].set_presence(e3.status.ONLINE)
        widget_dic['save_account_chk'].setChecked(False)
        widget_dic['save_password_chk'].setChecked(False)
        widget_dic['auto_login_chk'].setChecked(False)

    def _widget_status_refresh(self):
        print " *** _widget_status_refresh"
        ''' Checks wether each widget in the login page should be
        enabled or disabled, and changes its status accordingly'''
        widget_dic = self._widget_dic
        save_password_chk   = widget_dic['save_password_chk']
        login_btn           = widget_dic['login_btn']
        password_edit       = widget_dic['password_edit']
        presence_combo      = widget_dic['presence_combo']
        save_account_chk    = widget_dic['save_account_chk']
        auto_login_chk      = widget_dic['auto_login_chk']

        if self._is_account_valid:
            validity = True
            if self._is_there_a_password:
                save_password_chk.setEnabled(True)
                login_btn.setEnabled(True)
            else:
                save_password_chk.setEnabled(False)
                login_btn.setEnabled(False)
        else:
            validity = False
            login_btn.setEnabled(False)
        password_edit.setEnabled(validity)
        presence_combo.setEnabled(validity)
        save_account_chk.setEnabled(validity)
        #save_password_chk.setEnabled(validity)
        auto_login_chk.setEnabled(validity)


# -------------------- QT_OVERRIDE

    def eventFilter(self, obj, event):
        ''' event filter to handle return pression in the login window '''
        # pylint: disable=C0103
        if not obj == self:
            return False
        if event.type() == QtCore.QEvent.KeyRelease and \
            event.key() == Qt.Key_Return:
            self._widget_dic['login_btn'].animateClick()
            return True
        else:
            return False





GENERIC_DOMAINS = "aero", "asia", "biz", "cat", "com", "coop", \
    "edu", "gov", "info", "int", "jobs", "mil", "mobi", "museum", \
    "name", "net", "org", "pro", "tel", "travel"

def is_valid_mail(email_address, domains=GENERIC_DOMAINS):
    """Checks for a syntactically invalid email address.
    Taken from http://commandline.org.uk/python/email-syntax-check/"""

    # Email address must be 7 characters in total.
    if len(email_address) < 7:
        return False # Address too short.

    # Split up email address into parts.
    try:
        local_part, domain_name = email_address.rsplit('@', 1)
        host, top_level = domain_name.rsplit('.', 1)
    except ValueError:
        return False # Address does not have enough parts.

    # Check for Country code or Generic Domain.
    if len(top_level) != 2 and top_level not in domains:
        return False # Not a domain name.

    for i in '-_.%+.':
        local_part = local_part.replace(i, "")
    for i in '-_.':
        host = host.replace(i, "")

    if local_part.isalnum() and host.isalnum():
        return True # Email address is fine.
    else:
        return False # Email address has funny characters.
