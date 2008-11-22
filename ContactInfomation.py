import gtk

class ContactInformation(gtk.Window):
    '''a window that displays information about a contact'''

    def __init__(self, session, account):
        '''constructor'''
        gtk.Window.__init__(self)
        self.set_default_size(640, 480)

        self.tabs = gtk.Notebook()

        self._create_tabs()

    def _create_tabs(self):
        '''create all the tabs on the window'''
        self._create_info_tab()
        self._create_nicks_tab()
        self._create_messages_tab()
        self._create_status_tab()
        self._create_chat_tab()

    def _create_info_tab(self):
        '''create the tab that contains the information from the account'''
        pass

    def _create_nicks_tab(self):
        '''create the tab that contains the nicks from the account'''
        pass

    def _create_messages_tab(self):
        '''create the tab that contains the personal messages from the 
        account
        '''
        pass

    def _create_status_tab(self):
        '''create the tab that contains the status from the account'''
        pass

    def _create_chat_tab(self):
        '''create the tab that contains the  from the account'''
        pass

