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

import gui
from gui.base import MarkupParser
import utils

import glib
import gtk
import pango
import os
import Renderers

import logging
log = logging.getLogger('gui.gtkui.GtkNotification')

NAME = 'GtkNotification'
DESCRIPTION = 'emesene\'s notification system\'s gtk ui'
AUTHOR = 'arielj'
WEBSITE = 'www.emesene.org'


# This code is used only on Windows to get the location on the taskbar
if os.name == "nt":
    import ctypes
    from ctypes.wintypes import RECT
    user = ctypes.windll.user32

    # Find the window handler of the taskbar
    className = ctypes.c_wchar_p('Shell_TrayWnd')
    window = user.FindWindowExW(None, None, className, None)
    rect = RECT()
    user.GetWindowRect(window, ctypes.byref(rect))

    left = rect.left
    top = rect.top
    taskHeight = rect.bottom - top
    taskWidth = rect.right - left
    horizontal = taskHeight > taskWidth
    
    # Set values
    taskbarSide = "bottom"  # default windows xp values
    taskbarSize = 30 # default windows xp values
    if left == 0:
        if top == 0:
            if horizontal:
                taskbarSide = "top"
                taskbarSize = taskHeight
            else:
                taskbarSide = "left"
                taskbatSize = taskWidth
        else:
            taskbarSide = "bottom"
            taskbarSize = taskHeight
    else:
        taskbarSide = "right"
        taskbatSize = taskWidth

# Below, another method to get taskbar size and side
# I need to test both methods under Windows Vista and Windows 7
'''
    import ctypes
    from ctypes.wintypes import RECT, DWORD
    user = ctypes.windll.user32
    MONITORINFOF_PRIMARY = 1
    HMONITOR = 1

    class MONITORINFO(ctypes.Structure):
       _fields_ = [
            ('cbSize', DWORD),
            ('rcMonitor', RECT),
            ('rcWork', RECT),
            ('dwFlags', DWORD)
            ]

    taskbarSide = "bottom"
    taskbarSize = 30
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(info)
    info.dwFlags =  MONITORINFOF_PRIMARY
    user.GetMonitorInfoW(HMONITOR, ctypes.byref(info))
    if info.rcMonitor.bottom != info.rcWork.bottom:
        taskbarSize = info.rcMonitor.bottom - info.rcWork.bottom
    if info.rcMonitor.top != info.rcWork.top:
        taskbarSide = "top"
        taskbarSize = info.rcWork.top - info.rcMonitor.top
    if info.rcMonitor.left != info.rcWork.left:
        taskbarSide = "left"
        taskbarSize = info.rcWork.left - info.rcMonitor.left
    if info.rcMonitor.right != info.rcWork.right:
        taskbarSide = "right"
        taskbarSize = info.rcMonitor.right - info.rcWork.right
'''

queue = list()
actual_notification = None

def gtkNotification(title, text, picturePath=None, const=None, callback=None, tooltip=None):
    global actual_notification
    global queue

    # TODO: we can have an option to use a queue or show notifications
    # like the oldNotification plugin of emesene1.6 (WLM-like)

    if (const=='message-im'):
        #In this case title is contact nick
        title = Renderers.msnplus_to_plain_text(title)

    if actual_notification is None:
        actual_notification = Notification(title, text, picturePath, callback, tooltip)
        actual_notification.show()
    else:
        # Append text to the actual notification
        if actual_notification._title == title:
            actual_notification.append_text(text)
        else:
            found = False
            auxqueue = list()
            for _title, _text, _picturePath, _callback, _tooltip in queue:
                if _title == title:
                    _text = _text + "\n" + text
                    found = True
                auxqueue.append([_title,_text,_picturePath, _callback, _tooltip])

            if found:
                # append text to another notification
                del queue
                queue = auxqueue
            else:
                # or queue a new notification
                queue.append([title, text, picturePath, callback, tooltip])

class Notification(gtk.Window):
    def __init__(self, title, text, picturePath, callback, tooltip):

        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)

        # constants
        self.FColor = "white"
        BColor = gtk.gdk.Color()
        avatar_size = 48;
        max_width = 300;
        self.callback = callback

        # window attributes
        self.set_border_width(10)

        # labels
        self._title = title #nick
        markup1 = '<span foreground="%s" weight="ultrabold">%s</span>'
        titleLabel = gtk.Label(markup1 % (self.FColor, \
                               MarkupParser.escape(self._title)))
        titleLabel.set_use_markup(True)
        titleLabel.set_justify(gtk.JUSTIFY_CENTER)
        titleLabel.set_ellipsize(pango.ELLIPSIZE_END)

        self.text = text #status, message, etc...
        self.markup2 = '<span foreground="%s">%s</span>'
        self.messageLabel = gtk.Label(self.markup2 % (self.FColor, \
                                      MarkupParser.escape(self.text)))
        self.messageLabel.set_use_markup(True)
        self.messageLabel.set_justify(gtk.JUSTIFY_CENTER)
        self.messageLabel.set_ellipsize(pango.ELLIPSIZE_END)

        # image
        avatarImage = gtk.Image()
        try:
            userPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                                  picturePath[7:], avatar_size, avatar_size)
        except:
            userPixbuf = utils.safe_gtk_pixbuf_load(gui.theme.user,
                                                 (avatar_size, avatar_size))
        avatarImage.set_from_pixbuf(userPixbuf)

        # boxes
        hbox = gtk.HBox() # main box
        self.messageVbox = gtk.VBox() # title + message
        lbox = gtk.HBox() # avatar + title/message
        lbox.set_spacing(10)

        lboxEventBox = gtk.EventBox() # detects mouse events
        lboxEventBox.set_visible_window(False)
        lboxEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        lboxEventBox.connect("button_press_event", self.onClick)
        lboxEventBox.add(lbox)
        self.connect("button_press_event", self.onClick)

        if tooltip is not None:
            lboxEventBox.set_tooltip_text(tooltip)

        # pack everything
        self.messageVbox.pack_start(titleLabel, False, False)
        self.messageVbox.pack_start(self.messageLabel, True, True)
        lbox.pack_start(avatarImage, False, False)
        lbox.pack_start(self.messageVbox, True, True)
        hbox.pack_start(lboxEventBox, True, True)

        self.add(hbox)

        # change background color
        self.set_app_paintable(True)
        self.realize()
        self.window.set_background(BColor)

        # A bit of transparency to be less intrusive
        self.set_opacity(0.85)

        self.timerId = None
        self.set_default_size(max_width,-1)
        self.connect("size-allocate", self.relocate)
        self.show_all()

    def append_text(self, text):
        '''
        adds text at the end of the actual text
        '''
        self.text = self.text + "\n" + text
        self.messageLabel.set_text(self.markup2 % (self.FColor, \
                                   MarkupParser.escape(self.text)))
        self.messageLabel.set_use_markup(True)
        self.messageLabel.show()

    def relocate(self, widget=None, allocation=None):
        '''
        move notification to it's place
        '''

        width, height = self.get_size()
        # TODO: need config files for extension!
        gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.set_gravity(gravity)

        screen_w = gtk.gdk.screen_width()
        screen_h = gtk.gdk.screen_height()
        x = 0
        y = 0

        # move notification so taskbar won't hide it on Windows!
        if gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
            x = screen_w - width - 20
            y = screen_h - height - 10
            if os.name == "nt":
                if taskbarSide == "bottom":
                    y = screen_h - height - taskbarSize - 10
                elif taskbarSide == "right":
                    x = screen_w - width - taskbarSize
        elif gravity == gtk.gdk.GRAVITY_NORTH_EAST:
            x = screen_w - width - 10
            y = 10
            if os.name == "nt":
                if taskbarSide == "top":
                    y = taskbarSize
                elif taskbarSide == "right":
                    x = screen_w - width - taskbarSize
        elif gravity == gtk.gdk.GRAVITY_SOUTH_WEST:
            x = 10
            y = screen_h - height - 10
            if os.name == "nt":
                if taskbarSide == "bottom":
                    y = screen_h - height - taskbarSize
                elif taskbarSide == "left":
                    x = taskbarSize
        elif gravity == gtk.gdk.GRAVITY_NORTH_WEST:
            x = 10
            y = 10
            if os.name == "nt":
                if taskbarSide == "top":
                    y = taskbarSize
                elif taskbarSide == "left":
                    x = taskbarSize

        self.move(x,y)

    def onClick(self, widget, event):
        '''
        action to be done if user click's the notification
        '''
        if self.callback is not None:
            self.callback()
        self.close()

    def show(self):
        ''' show it and run the timeout'''
        self.show_all()
        self.timerId = glib.timeout_add_seconds(10, self.close)
        return True

    def close(self, *args):
        ''' hide the Notification and show the next one'''
        global actual_notification
        global queue

        self.hide()
        if self.timerId is not None:
            glib.source_remove(self.timerId)
        if len(queue) != 0:
            title, text, picturePath, callback, tooltip = queue.pop(0)
            actual_notification = Notification(title, text, picturePath, \
                                               callback, tooltip)
            actual_notification.show()
        else:
            actual_notification = None
        self.destroy()
