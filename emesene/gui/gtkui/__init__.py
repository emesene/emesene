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

import extension

WEBKITERROR = False
INFOBARERROR = False

def gtk_main(Controller):
    """ main method for gtk frontend
    """
    global WEBKITERROR, INFOBARERROR

    import gtk
    import gobject

    import AccountMenu
    import Avatar
    import AvatarChooser
    import AvatarManager
    import CallWidget
    import ContactMenu
    import ContactList
    import SyncTool
    import ContactInfoRotate
    import ContactInfoList
    import Conversation
    import ConversationManager
    import ConversationToolbar
    import DebugWindow
    import Dialog
    import EmptyWidget
    import FileTransferBarWidget
    import FileTransferWidget
    import GroupMenu

    import Header
    if not check_gtk3():
        import ImageAreaSelector
    else:
        import ImageAreaSelectorNew as ImageAreaSelector

    import Login
    import MainMenu
    import MainWindow
    import MarkupParser

    try:
        import InfoBar
    except ImportError:
        INFOBARERROR = True
    import NiceBar

    import PluginWindow
    import Preferences

    if not check_gtk3():
        import Renderers
    else:
        import RenderersNew as Renderers

    import StatusMenu
    import TabWidget
    import TextBox
    import UserPanel
    import Window

    try:
        import AdiumTextBox
    except ImportError:
        WEBKITERROR = True

    import PictureHandler

    setup()
    gobject.threads_init()
    gtk.gdk.threads_init()
    gtk.gdk.threads_enter()
    controller = Controller()
    controller.start()
    extension.set_default('quit', gtk.main_quit)
    gtk.main()
    gtk.gdk.threads_leave()


gtk_main.NAME = "Gtk main function"
gtk_main.DESCRIPTION  = "This extensions uses Gtk to build the GUI"
gtk_main.AUTHOR = "marianoguerra"
gtk_main.WEBSITE = "emesene.org"

extension.category_register('main', gtk_main)

def setup():
    """
    define all the components for a gtk environment
    """
    global WEBKITERROR, INFOBARERROR

    import gtk
    gtk.settings_get_default().set_property("gtk-error-bell", False)

    extension.register('quit', gtk.main_quit)

    extension.category_register('dialog', Dialog.Dialog)
    extension.category_register('avatar chooser', AvatarChooser.AvatarChooser)
    extension.category_register('avatar', Avatar.Avatar)
    extension.category_register('avatar manager', AvatarManager.AvatarManager)

    extension.category_register('preferences', Preferences.Preferences,
            single_instance=True)
    extension.category_register('login window', Login.Login)
    extension.category_register('connecting window', Login.ConnectingWindow)
    extension.category_register('window frame', Window.Window)
    extension.category_register('main window', MainWindow.MainWindow)
    extension.category_register('contact list', ContactList.ContactList)
    extension.category_register('synch tool', SyncTool.SyncTool)
    if not check_gtk3():
        extension.category_register('avatar renderer', Renderers.AvatarRenderer)
        extension.category_register('nick renderer', Renderers.CellRendererPlus)
        extension.register('nick renderer', Renderers.CellRendererNoPlus)
    else:
        extension.category_register('avatar renderer', RenderersNew.AvatarRenderer)
        extension.category_register('nick renderer', RenderersNew.CellRendererPlus)
        extension.register('nick renderer', RenderersNew.CellRendererNoPlus)

    extension.category_register('user panel', UserPanel.UserPanel)

    extension.category_register('debug window', DebugWindow.DebugWindow)

    if not INFOBARERROR:
        extension.category_register('nice bar', InfoBar.NiceBar)
        extension.register('nice bar', NiceBar.NiceBar)
    else:
        extension.category_register('nice bar', NiceBar.NiceBar)

    extension.category_register('main menu', MainMenu.MainMenu)
    extension.category_register('menu file', MainMenu.FileMenu)
    extension.category_register('menu actions', MainMenu.ActionsMenu)
    extension.category_register('menu options', MainMenu.OptionsMenu)
    extension.category_register('menu contact', ContactMenu.ContactMenu)
    extension.category_register('menu group', GroupMenu.GroupMenu)
    extension.category_register('menu account', AccountMenu.AccountMenu)
    extension.category_register('menu help', MainMenu.HelpMenu)
    extension.category_register('menu status', StatusMenu.StatusMenu)

    extension.category_register('below menu', EmptyWidget.EmptyWidget)
    extension.category_register('below panel', EmptyWidget.EmptyWidget)
    extension.category_register('below userlist', EmptyWidget.EmptyWidget)

    extension.category_register('call widget', CallWidget.CallWindow)
    extension.category_register('conversation window', \
        ConversationManager.ConversationManager)
    extension.category_register('conversation', Conversation.Conversation)
    extension.category_register('conversation header', Header.Header)
    extension.category_register('conversation info',
                                ContactInfoRotate.ContactInfoRotate)
    extension.register('conversation info', ContactInfoList.ContactInfoList)
    extension.category_register('conversation tab', TabWidget.TabWidget)
    extension.category_register('conversation input', TextBox.InputText)
    extension.category_register('conversation toolbar', \
        ConversationToolbar.ConversationToolbar)
    extension.category_register('plugin window', \
        PluginWindow.PluginWindow)
    if not check_gtk3():
        extension.category_register('image area selector', ImageAreaSelector.ImageAreaSelectorDialog)
    else:
        extension.category_register('image area selector', ImageAreaSelectorNew.ImageAreaSelectorDialog)
    extension.category_register('filetransfer pool', FileTransferBarWidget.FileTransferBarWidget)
    extension.category_register('filetransfer widget', FileTransferWidget.FileTransferWidget)

    if not WEBKITERROR:
        extension.category_register('conversation output', AdiumTextBox.OutputText)
        extension.register('conversation output', TextBox.OutputText)
    else:
        extension.category_register('conversation output', TextBox.OutputText)

    extension.category_register('picture handler', PictureHandler.PictureHandler)

def check_gtk3():
    '''return true if it's gtk3'''
    import gtk
    return gtk.pygtk_version[0] == 2 and gtk.pygtk_version[1] == 99
