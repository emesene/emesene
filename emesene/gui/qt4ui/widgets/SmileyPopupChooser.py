# -*- coding: utf-8 -*-

'''This modulke contains the SmileyPopupChooser class'''

import math

import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui


class SmileyPopupChooser (QtGui.QDockWidget):
    '''This class represents a popup border-less smiley chooser, which 
    disappears 200ms after the mouse leaves it. It handles its positioning
    in a way such that it never appears off-screen'''
    # pylint: disable=W0612
    NAME = 'MainPage'
    DESCRIPTION = 'The widget used to to select an emoticon'
    AUTHOR = 'Gabriele "Whisky" Visconti'
    WEBSITE = ''
    # pylint: enable=W0612
    
    _FADE_TIME = 200
    emoticon_selected = QtCore.pyqtSignal('QString')
    
    def __init__(self, parent=None):
        '''Constructor'''
        QtGui.QDockWidget.__init__(self, parent, Qt.Popup)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._fade_timer = QtCore.QTimer()
        self._fade_timer.setSingleShot(False)

        emote_theme = gui.theme.emote_theme
        smiley_dict = emote_theme.get_emotes()
        smiley_button_list = []
        added_smileys = []
    
        for shortcut, name in smiley_dict.iteritems():
            # avoid doubled smileys:
            if name in added_smileys:
                continue
            added_smileys.append(name)
            icon_path = emote_theme.emote_to_path(shortcut)
            if not icon_path:
                continue
            icon_path = icon_path[6:]
            icon = QtGui.QIcon(icon_path)
            button = SmileyButton(icon, name, shortcut)
            button.setFlat(True)
            width, height = button.size().width(), button.size().height()
            button.resize(min(width, height), min(width, height))
            button.selected.connect(self._on_emoticon_selected)
            smiley_button_list.append(button)
            
        #calculate dimensions:
        # constraints: x*y = len(smiley_dict) = r AND  x/y = 1.6
        # which gives: y = sqrt(num_elems/r) AND x = sqrt(r*num_elems)
        num_elems = len(smiley_button_list)
        # number of columns:
        self.num_columns = math.ceil(
                            math.sqrt(1.6 * num_elems))
        # number of rows:
        self.num_rows = math.ceil(num_elems / self.num_columns)
        # convert these two float numbers into integers:
        self.num_columns = math.trunc(self.num_columns)
        self.num_rows    = math.trunc(self.num_rows)
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(0)
        counter = 0
        for i in range(self.num_rows):
            for j in range(self.num_columns):
                if counter >= num_elems:
                    continue
                grid.addWidget(smiley_button_list[counter], i,  j)
                counter += 1

        central_widget = QtGui.QWidget()
        central_widget.setLayout(grid)
        
        self.setWidget(QtGui.QWidget())
        self.setFeatures(QtGui.QDockWidget.NoDockWidgetFeatures)
        self.setTitleBarWidget(central_widget)
        
        self._timer.timeout.connect(self.fade_out)
        self._fade_timer.timeout.connect(self.fade_out)
        

    def _on_emoticon_selected(self, shortcut):
        '''Slot called when the user selects an emoticon'''
        self.hide()
        self.emoticon_selected.emit(shortcut)
        
    def fade_out(self):
        '''Fades out the popup smoothly'''
        opacity = self.windowOpacity()
        opacity -= 0.1
        
        if opacity > 0.2:
            self.setWindowOpacity(self.windowOpacity() - 0.1)
            if not self._fade_timer.isActive():
                self._fade_timer.start(self._FADE_TIME / 9)
        else:
            self.hide()
            self.setWindowOpacity(1)
            self._fade_timer.stop()

# -------------------- QT_OVERRIDE
        
    def enterEvent(self, event):
        '''If the timer started by leaveEvent is active, stops it'''
        # pylint: disable=C0103
        if self._timer.isActive():
            self._timer.stop()
        QtGui.QDockWidget.enterEvent(self, event)
        
    def leaveEvent(self, event):
        '''Starts a 750ms timer. When the timer runs out of time,
        the widget starts to fade_out'''
        # pylint: disable=C0103
        self._timer.start(750)
        QtGui.QDockWidget.leaveEvent(self, event)
        
    def show(self):
        '''Shows the widget, making sure it doesn't appear off-screen'''
        # pylint: disable=C0103
        pos = QtGui.QCursor.pos()
        x_pos = pos.x()
        y_pos = pos.y()
        
        q_app = QtGui.QApplication.instance()
        screen_geometry = q_app.desktop().screenGeometry()
        max_x = screen_geometry.width()
        max_y = screen_geometry.height()
        
        my_size = self.sizeHint()
        delta_x = my_size.width()
        delta_y = my_size.height()
        
        if (x_pos + delta_x) > max_x:
            x_pos = max_x - delta_x
        if (y_pos + delta_y) > max_y:
            y_pos = max_y - delta_y
        
        self.move(QtCore.QPoint(x_pos, y_pos))
        QtGui.QDockWidget.show(self)
    




class SmileyButton (QtGui.QPushButton):
    '''This class represents a single smiley button in the 
    smiley chooser panel.
    This is a KPushButton with the shortcut as tooltip, and 
    fixed dimension.'''
    selected = QtCore.pyqtSignal('QString')
    def __init__(self, icon, tooltip, shortcut,  parent=None):
        '''Constructor'''
        QtGui.QPushButton.__init__(self, icon, QtCore.QString(), )
        self.setToolTip('<b>%s</b> %s' % (shortcut, tooltip) )
        self.shortcut = QtCore.QString(shortcut)
        self.clicked.connect(self._emit_signal)
        
    def _emit_signal(self):
        '''Slot called when this button is clicked.
        Emits a "selected" signal with the shortcut as argument'''
        self.selected.emit(self.shortcut)
        
# -------------------- QT_OVERRIDE
        
    def sizeHint(self):
        '''Returns a fixed size hint'''
        # pylint: disable=C0103
        return QtCore.QSize(25, 25)
