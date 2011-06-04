'''a tool to call the synch procedure'''
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

from e3.synch.synchronizer import *
import gui
import extension
import utils

class SyncTool(object):
    '''a tool to call the synch procedure'''
    NAME = 'Synch tool'
    DESCRIPTION = 'A tool to show a dialog to launch synch procedure'
    AUTHOR = 'Andrea Stagi'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session, synch_type):
        '''class constructor'''
        self.ENABLE = True # Enabled. Set False for disable.
        self._session = session
        self._syn = get_synchronizer(synch_type)
        self._syn.set_user(self._session._account.account)

    def show(self, show_second_time = False):
        '''called when you want to show synch dialog'''

        if not self._syn.exists_source():
            return

        if not self._syn.is_clean():
            self._show_dialog()

        elif not self._session.config.get_or_set("logs_imported", False):
            self._show_dialog()

        elif show_second_time == True:
                self._show_dialog()

    def _show_finish(self, result):
        '''called to show a message of finish'''
        if result[0]:
            self.progress.set_action(_("Synchronization finished"))
            self._session.config.logs_imported = True
            self.progress.update(100.0)
            self._syn.clean()
        else:
            self.progress.set_action(_("Synchronization ERROR"))


    def _update_progress(self, progress):
        '''called everytime sync make a progress'''
        self.progress.update(progress)

    def _update_action(self, action):
        '''called everytime sync changes action'''
        self.progress.set_action(action)

    def _show_dialog(self):
        '''called to show dialog'''
        if self.ENABLE == False:
            return
        dialog = extension.get_default('dialog')
        dialog.yes_no_cancel(
            _("Do you want to synchronize with emesene 1?"), self._synch_cb)


    def _synch_cb(self, response):
        '''callback for DialogManager.yes_no, asking to synch'''
        if response == gui.stock.YES:
            dialog = extension.get_default('dialog')

            self.progress = dialog.sync_progress_window(
                _('Synchronization progress'), self._synch_progress_cb)

            self._syn.initialize(self._session, self._show_finish,
                                 self._update_progress, self._update_action)

            utils.GtkRunner(self._syn._end_callback, self._syn.start_synch)

        elif response == gui.stock.NO:
            self._session.config.logs_imported = True
            
            if not self._syn.is_clean():
                self._syn.clean()

            
    def _synch_progress_cb(self, event, response = None):
        '''stop synch'''
        self._syn.stop_synch()

