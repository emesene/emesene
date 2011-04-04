from e3.synch.synchronizer import *
import gui
import extension

class SyncTool(object):
    '''a tool to call the synch procedure'''
    NAME = 'Synch tool'
    DESCRIPTION = 'A tool to show a dialog to launch synch procedure'
    AUTHOR = 'Andrea Stagi'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, synch_type):
        '''class constructor'''
        self._session = session
        self._syn = get_synchronizer(synch_type)
        self._syn.set_user(self._session._account.account)


    def show(self):
        '''called when you want to show synch dialog'''
        if not self._session.config.get_or_set("logs_imported",False) and self._syn.exists_source():
            self._show_dialog()
            return
        if self._session.config.get_or_set("synch_retry",False):
            self._show_dialog()
            return


    def _show_dialog(self):
        '''called to show dialog'''
        dialog = extension.get_default('dialog')
        dialog.yes_no_cancel(
            _("Do you want to synch with emesene 1?"), self._synch_cb)


    def _synch_cb(self, response):
        '''callback for DialogManager.yes_no, asking to synch'''
        if response == gui.stock.YES:
            self._syn.start_synch(self._session)
            self.session.config.logs_imported = True
            self.session.config.get_or_set("synch_retry",False)

        elif response == gui.stock.NO:
            self.session.config.logs_imported = True
            self.session.config.get_or_set("synch_retry",True)

