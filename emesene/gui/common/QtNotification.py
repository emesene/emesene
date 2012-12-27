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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from gui.base import Plus

queue = list()
actual_notification = None

def QtNotification(title, text, picture_path=None, const=None,
                    callback=None, tooltip=None):
    global actual_notification
    global queue

    if (const=='message-im'):
        #In this case title is contact nick
        title = Plus.msnplus_strip(title)

    if actual_notification is None:
        actual_notification = Notification(title, text, picture_path, callback,
                                           tooltip)
        actual_notification.show()
    else:
        # Append text to the actual notification
        if actual_notification._caption == title:
            actual_notification.append_text(text)
        else:
            found = False
            auxqueue = list()
            for _title, _text, _picture_path, _callback, _tooltip in queue:
                if _title == title:
                    _text = _text + "\n" + text
                    found = True
                auxqueue.append([_title,_text,_picture_path, _callback,
                                 _tooltip])

            if found:
                # append text to another notification
                del queue
                queue = auxqueue
            else:
                # or queue a new notification
                queue.append([title, text, picture_path, callback, tooltip])

class Notification(QDialog):
    def __init__(self, title, text, picture_path=None, const=None,
                   callback=None, tooltip=None):
        parent = QApplication.desktop()
        super(Notification,  self).__init__(parent)

        self.parent = parent
        self.setWindowFlags(Qt.Tool| Qt.X11BypassWindowManagerHint | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity (0.7)
        self.setStyleSheet("QDialog { background-color: black;} QLabel{color: white;}")
        #self.setToolTip(tooltip)
        self.__parent = parent

        if const == 'message-im':
            #In this case title is contact nick
            if title is None:
                title = ""
            title = Plus.msnplus_strip(title)

        self._caption = unicode(title)
        self.__text = unicode(text, "utf8")
        self.__icon = QPixmap(picture_path[7:])
        self.__pos = QPoint(0,  0)
        self.connect(self, SIGNAL("clicked()"), SLOT("close()"))
        self.showPopup()

    def showPopup(self):

        caption = self._caption
        text = self.__text
        icon = self.__icon

        hb = QHBoxLayout(self)
        hb.setMargin(8)
        hb.setSpacing(6)

        vb = QVBoxLayout()
        vb.setMargin(8)
        vb.setSpacing(6)

        ttlIcon = QLabel()
        ttlIcon.setPixmap(icon)
        ttlIcon.setAlignment(Qt.AlignLeft)
        hb.addWidget(ttlIcon)

        ttl = QLabel("<b>" + caption + "</b>")
        fnt = ttl.font()
        fnt.setBold(True)
        ttl.setFont(fnt)
        ttl.setAlignment(Qt.AlignHCenter)
        vb.setStretchFactor(ttl,  10)
        vb.addWidget(ttl)

        self.msg = QLabel(text)
        self.msg.setAlignment(Qt.AlignLeft)
        self.msg.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.msg.setOpenExternalLinks(True)
        vb.addWidget(self.msg)

        hb.addLayout(vb)

        self.__moveNear()

    def __moveNear(self):
        r = QApplication.desktop().geometry()

        # put notification on bottom-left corner
        y = r.bottom() - self.minimumSizeHint().height()
        x = r.right() - self.minimumSizeHint().width()

        if y < r.top():
            y = r.top()

        if x < r.left():
            x = r.left()

        #XXX: left some space for panel
        y = y - 40

        self.move(QPoint(x,  y))

    def mouseReleaseEvent(self,  e):
        self.emit(SIGNAL("clicked()"))
        self.emit(SIGNAL("clicked(QPoint)"),  e.pos())

    def append_text(self, text):
        '''
        adds text at the end of the actual text
        '''
        self.__text = self.__text + "\n" + text
        self.msg.setText(self.__text)
        #relocate
        self.__moveNear()

    def show(self):
        ''' show it and run the timeout'''
        super(Notification,  self).show()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)
        self.timer.start(5000)

    def close(self, *args):
        ''' hide the Notification and show the next one'''
        global actual_notification
        global queue

        self.hide()
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

        if len(queue) != 0:
            title, text, picture_path, callback, tooltip = queue.pop(0)
            actual_notification = Notification(title, text, picture_path,
                                               callback, tooltip)
            actual_notification.show()
        else:
            actual_notification = None
        super(Notification,  self).close()
