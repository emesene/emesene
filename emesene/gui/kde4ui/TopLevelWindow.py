# -*- coding: utf-8 -*-

''' This module contains the top level window class '''

import PyKDE4.kdeui as kdeui
import PyQt4.QtGui as QtGui
import extension

class TopLevelWindow (kdeui.KMainWindow):
    ''' Class representing the main window '''
    # pylint: disable=W0612
    NAME = 'TopLevelWindow'
    DESCRIPTION = 'The window used to contain all the content of emesene'
    AUTHOR = 'Gabriele Whisky Visconti'
    WEBSITE = ''
    # pylint: enable=W0612

    def __init__(self, cb_on_close):
        kdeui.KMainWindow.__init__(self)
        self._content_type = 'empty'
        if cb_on_close:
            self._cb_on_close = cb_on_close
        else: # we're the main window
            self._cb_on_close = self.hide

        self.setObjectName('mainwindow')
        self.setWindowIcon(kdeui.KIcon('im-user'))
        self._page_stack = QtGui.QStackedWidget()
        self.setCentralWidget(self._page_stack)

    def clear(self): #emesene's
        '''remove the content from the main window'''
        pass

    def set_location(self, width, height, posx, posy): #emesene's
        '''Sets size and position on screen '''
        self.resize(width, height)
        self.move(posx, posy)

    def _get_content_type(self):
        ''' Getter method for "content_type" property'''
        return self._content_type

    content_type = property(_get_content_type) #emesene's

    def get_dimensions(self): #emesene's
        '''
        Returns a tuple containing width, height, x coordinate, y coordinate
        '''
        size = self.size()
        position = self.pos()
        return size.width(), size.height(), position.x(), position.y()

    def go_connect(self, on_cancel_login, avatar_path, config):
        '''does nothing'''
        print "GO CONNECT! ^_^"

    def go_login(self, callback, on_preferences_changed,
           config=None, config_dir=None, config_path=None,
           proxy=None, use_http=None, session_id=None, cancel_clicked=False):
               #emesene's
        # pylint: disable=R0913
        '''add a login page to the top level window and shows it'''
        login_window_cls = extension.get_default('login window')
        login_page = login_window_cls(callback, on_preferences_changed,
                                      config, config_dir, config_path, proxy,
                                      use_http, session_id, cancel_clicked)
        self._switch_to_page(login_page)

#    def setMenu(self, menuBar):
#        KFELog().l("KFEMainWindow.setMenu()")
#        self.setMenuBar(menuBar)
#
#    def setTitle(self, title):
#        KFELog().l("KFEMainWindow.setTitle()")
#        self.setPlainCaption(title)
#
#    def show(self):
#        KFELog().l("KFEMainWindow.show()")
#        KMainWindow.show(self)
#        self.onMainWindowShown()
#
    def _switch_to_page(self, page_widget):
        ''' Shows the given page '''
        index = self._page_stack.indexOf(page_widget)
        if index == -1:
            index = self._page_stack.addWidget(page_widget)
        self._page_stack.setCurrentIndex(index)


# -------------------- QT_OVERRIDE

    def closeEvent(self, event):
        # pylint: disable=C0103
        ''' Overrides KMainWindow's close event '''
        self._cb_on_close()
        event.accept()
        #self.onClose()
