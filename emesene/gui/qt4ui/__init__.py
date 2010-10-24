# -*- coding: utf-8 -*-

'''
Module containing frontend initialization function, and frontend main loop
'''

import extension

GCONTEXT = None

from gui.qt4ui.Utils import pixmap_rounder



def qt4_main(controller_cls):
    """ main method for Qt4 frontend
    """

    import gobject
    global GCONTEXT
    GCONTEXT = gobject.MainLoop().get_context()


    import os
    import sys
    import PyQt4.QtCore     as QtCore
    import PyQt4.QtGui      as QtGui

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
    import Notifier
    import TopLevelWindow
    import TrayIcon
    import pages
    import widgets

    extension.category_register('conversation window', pages.ConversationPage)
    extension.category_register('contact list', widgets.ContactList)
    extension.category_register('login window', pages.LoginPage)
    extension.category_register('main window', pages.MainPage)
    extension.category_register('notificationGUI', Notifier.Notifier)
    extension.category_register('window frame', TopLevelWindow.TopLevelWindow)
    extension.category_register('tray icon',    TrayIcon.TrayIcon)



def on_idle():
    '''When there's nothing to do in the Qt event loop
    process events in the gobject event queue'''
    while GCONTEXT.pending():
        GCONTEXT.iteration()

