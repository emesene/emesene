# -*- coding: utf-8 -*-

'''
Module containing frontend initialization function, and frontend main loop
'''

import extension

GCONTEXT = None



def kde4_main(controller_cls):
    """ main method for kde4 frontend
    """

    import gobject
    global GCONTEXT
    GCONTEXT = gobject.MainLoop().get_context()


    import os
    import sys
    import PyKDE4.kdeui     as KdeGui
    import PyKDE4.kdecore   as KdeCore
    import PyQt4.QtCore     as QtCore

    setup()
    os.putenv('QT_NO_GLIB', '1')
    about_data = KdeCore.KAboutData("emesene", "",
                                   KdeCore.ki18n("emesene"), "0.001")
    KdeCore.KCmdLineArgs.init(sys.argv[2:], about_data)
    app = KdeGui.KApplication()
    idletimer = QtCore.QTimer(KdeGui.KApplication.instance())
    idletimer.timeout.connect(on_idle)
    idletimer.start(100)

    controller = controller_cls()
    controller.start()

    app.exec_()


# pylint: disable=W0612
kde4_main.NAME = "kde4_main"
kde4_main.DESCRIPTION  = "This extensions uses KDElibs/Qt to build the GUI"
kde4_main.AUTHOR = "Gabriele Whisky Visconti"
kde4_main.WEBSITE = ""
# pylint: enable=W0612

extension.register('main', kde4_main)

def setup():
    """
    define all the components for a kde4 environment
    """
    # pylint: disable=W0403
    import TopLevelWindow
    import TrayIcon
    import pages

    extension.category_register('login window', pages.LoginPage)
    extension.category_register('window frame', TopLevelWindow.TopLevelWindow)
    extension.category_register('tray icon',    TrayIcon.TrayIcon)



def on_idle():
    '''When there's nothing to do in the Qt event loop
    process events in the gobject event queue'''
    iterations = 0
    while iterations < 10 and GCONTEXT.pending():
        GCONTEXT.iteration()
        iterations += 1

