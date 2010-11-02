# -*- coding: utf-8 -*-

'''
Module containing frontend initialization function, and frontend main loop
'''

import extension



GCONTEXT = None

def qt4_main(controller_cls):
    """ main method for Qt4 frontend
    """

    import os
    import sys
    
    import gobject
    
    import PyQt4.QtCore     as QtCore
    import PyQt4.QtGui      as QtGui
    
    global GCONTEXT
    GCONTEXT = gobject.MainLoop().get_context()
    
    reload(sys)
    sys.setdefaultencoding("utf8")
    
    setup()
    
    os.putenv('QT_NO_GLIB', '1')
    #about_data = KdeCore.KAboutData("emesene", "",
                                   #KdeCore.ki18n("emesene"), "0.001")
    #KdeCore.KCmdLineArgs.init(sys.argv[2:], about_data)
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('emesene2')
    
    idletimer = QtCore.QTimer(QtGui.QApplication.instance())
    idletimer.timeout.connect(on_idle)
    idletimer.start(10)

    controller = controller_cls()
    controller.start()

    app.exec_()


# pylint: disable=W0612
qt4_main.NAME = "qt4_main"
qt4_main.DESCRIPTION  = "This extensions uses Qt to build the GUI"
qt4_main.AUTHOR = "Gabriele Whisky Visconti"
qt4_main.WEBSITE = ""
# pylint: enable=W0612

extension.register('main', qt4_main)

def setup():
    """
    define all the components for a Qt4 environment
    """
    # pylint: disable=W0403
    import Conversation
    import Dialog
    import Notifier
    import PictureHandler
    import TopLevelWindow
    import TrayIcon
    import menus
    import pages
    import widgets

    
    extension.category_register('conversation',     Conversation.Conversation)
    extension.category_register('dialog',           Dialog.Dialog)
    extension.category_register('notificationGUI',  Notifier.Notifier)
    extension.category_register('window frame',  TopLevelWindow.TopLevelWindow)
    extension.category_register('tray icon',        TrayIcon.TrayIcon)

    extension.category_register('conversation window', pages.ConversationPage)
    extension.category_register('login window',        pages.LoginPage)
    extension.category_register('main window',         pages.MainPage)
    
    
    extension.category_register('contact list',        widgets.ContactList)
    extension.category_register('conversation input',  widgets.ChatInput)
    extension.category_register('conversation output', widgets.ChatOutput)
    extension.category_register('avatar',              widgets.DisplayPic)
    extension.category_register('nick edit',           widgets.NickEdit)
    extension.category_register('smiley chooser',   widgets.SmileyPopupChooser)
    extension.category_register('status combo',        widgets.StatusCombo)
    extension.category_register('info panel',          widgets.UserInfoPanel)
    
    extension.category_register('main menu',    menus.MainMenu)
    extension.category_register('menu file',    menus.FileMenu)
    extension.category_register('menu actions', menus.ActionsMenu)
    extension.category_register('menu options', menus.OptionsMenu)
    extension.category_register('menu help',    menus.HelpMenu)
    
    extension.category_register('menu contact', menus.ContactMenu)
    extension.category_register('menu group',   menus.GroupMenu)
    extension.category_register('menu profile', menus.ProfileMenu)
    extension.category_register('menu status',  menus.StatusMenu)
    
    extension.category_register('tray main menu',  menus.TrayMainMenu)
    extension.category_register('tray login menu', menus.TrayLoginMenu)
    
    extension.category_register('picture handler', 
                                PictureHandler.PictureHandler)
    

    
    
    


def on_idle():
    '''When there's nothing to do in the Qt event loop
    process events in the gobject event queue'''
    while GCONTEXT.pending():
        GCONTEXT.iteration()

