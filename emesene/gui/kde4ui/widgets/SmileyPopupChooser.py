# -*- coding: utf-8 -*-

import PyKDE4.kdeui     as KdeGui
import PyQt4.QtGui      as QtGui
import PyQt4.QtCore     as QtCore
from PyQt4.QtCore   import Qt

import gui

import math


class SmileyPopupChooser (QtGui.QDockWidget):
    _FADE_TIME = 200
    emoticon_selected = QtCore.pyqtSignal("QString")
    
    def __init__(self, parent=None):
        QtGui.QDockWidget.__init__(self, parent, Qt.Popup)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._fade_timer = QtCore.QTimer()
        self._fade_timer.setSingleShot(False)

        smiley_dict = gui.theme.EMOTES
        smiley_button_list = []
    
        for i in smiley_dict.keys():
            icon_path = gui.theme.emote_to_path(i)
            if not icon_path:
                continue
            icon_path = icon_path[6:]
            icon = KdeGui.KIcon(QtGui.QIcon(icon_path))
            button = SmileyButton(icon, smiley_dict[i],  i)
            button.setFlat(True)
            width, height = button.size().width(), button.size().height()
            button.resize(min(width, height), min(width, height))
            button.selected.connect(self._on_emoticon_selected)
            smiley_button_list.append(button)
            
        #calculate dimensions:
        # constraints: x*y = len(smiley_dict) = r AND  x/y = 1.6
        # which gives: y = sqrt(p/r) AND x = sqrt(r*p)
        p = len(smiley_button_list)
        self.num_columns = math.ceil(math.sqrt(1.6 * p)) #numero di colonne
        self.num_rows = p / self.num_columns #numero di righe
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(0)
        counter = 0
        for i in range(self.num_rows):
            for j in range(self.num_columns):
                if counter >= p:
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
        
    def enterEvent(self, event):
        if self._timer.isActive():
            self._timer.stop()
        
    def leaveEvent(self, event):
        self._timer.start(750)
        
    def _on_emoticon_selected(self, shortcut):
        '''Slot called when the user selects an emoticon'''
        self.hide()
        self.emoticon_selected.emit(shortcut)
        
    def show(self):
        pos = QtGui.QCursor.pos()
        x_pos = pos.x()
        y_pos = pos.y()
        
        k_app = KdeGui.KApplication.kApplication()
        screen_geometry = k_app.desktop().screenGeometry()
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
    
    def fade_out(self):
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




class SmileyButton (KdeGui.KPushButton):
    '''This class represents a single smiley button in the 
    smiley chooser panel.
    This is a KPushButton with the shortcut as tooltip, and 
    fixed dimension.'''
    selected = QtCore.pyqtSignal("QString")
    def __init__(self, icon, tooltip, shortcut,  parent=None):
        '''Constructor'''
        KdeGui.KPushButton.__init__(self, icon, QtCore.QString(), )
        self.setToolTip("<b>%s</b> %s" % (shortcut, tooltip) )
        self.shortcut = QtCore.QString(shortcut)
        self.clicked.connect(self._emit_signal)
        
    def _emit_signal(self):
        '''Slot called when this button is clicked.
        Emits a "selected" signal with the shortcut as argument'''
        self.selected.emit(self.shortcut)
        
    def sizeHint(self):
        return QtCore.QSize(25, 25)
