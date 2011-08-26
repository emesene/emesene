'''module to define the ExtensionsDownloader class, used by plugin.py'''
import gtk
import gobject

import e3
import gui
import extension
from gui.gtkui import utils

from DownloadExtension import DownloadExtension
from Collections import ThemesCollection
from Collections import PluginsCollection

class ExtensionsDownloader():
    """a plugin to download themes"""
    NAME = 'Extensions Downloader'
    DESCRIPTION = 'A plugin to download themes'
    AUTHOR = 'Andrea Stagi'
    WEBSITE = 'www.emesene.org'

    def __init__(self, session):
        """constructor"""
        self.session = session
        self.instance = extension.get_and_instantiate('preferences', self.session)

        if self.session is not self.instance.session:
            extension.delete_instance('preferences')
            self.instance = extension.get_and_instantiate('preferences', self.session)

        self.page_thm = DownloadExtension(self.session, 'emesene-community-themes', 'emesene-supported-themes', 4, ThemesCollection)
        self.page_plg = DownloadExtension(self.session, 'emesene-community-plugins', 'emesene-supported-plugins', 1, PluginsCollection)


    def add_to_main_list(self):
        self.instance.add_to_list(gtk.STOCK_NETWORK, _('Download themes'), self.page_thm)
        self.instance.add_to_list(gtk.STOCK_NETWORK, _('Download plugins'), self.page_plg)


    def remove_from_main_list(self):
        self.instance.remove_from_list(gtk.STOCK_NETWORK, _('Download themes'), self.page_thm)
        self.instance.remove_from_list(gtk.STOCK_NETWORK, _('Download plugins'), self.page_plg)
        

    def on_status_changed(self , *args):
        """called when a status is selected"""
        stat = self.model.get(self.get_active_iter(), 1)[0]

        if self.status != stat:
            self.status = stat
            self.main_window.session.set_status(stat)


    def on_status_change_succeed(self, stat):
        """called when the status was changed on another place"""
        if stat in e3.status.ORDERED:
            self.status = stat
            index = e3.status.ORDERED.index(stat)
            self.set_active(index)


    def on_scroll_event(self, button, event):
        """called when a scroll is made over the combo"""
        self.popup()
        return True
