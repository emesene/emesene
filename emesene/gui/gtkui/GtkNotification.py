import gui
from gui.base import MarkupParser
import utils

import glib
import gtk
import pango
import os

import logging
log = logging.getLogger('gui.gtkui.GtkNotification')

NAME = 'GtkNotification'
DESCRIPTION = 'Emesene\'s notification system\'s gtk ui'
AUTHOR = 'arielj'
WEBSITE = 'www.emesene.org'


# This code is used only on Windows to get the location on the taskbar
if os.name == "nt":
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

queue = list()
actual_notification = None

def gtkNotification(title, text, picturePath=None):
    global actual_notification

    # TODO: we can have an option to use a queue or show notifications
    # like the oldNotification plugin of emesene1.6 (WLM-like)

    # use a notification queue, like pynotify
    if actual_notification is None:
        actual_notification = Notification(title, text, picturePath)
        actual_notification.show()
    else:
        # TODO: check the other notifications and append the text to the
        # corresponding one
        if actual_notification._title == title:
            actual_notification.append_text(text)
        else:
            queue.append([title,text,picturePath])

class Notification(gtk.Window):
    def __init__(self, title, text, picturePath):

        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)

        # constants
        self.FColor = "white"
        BColor = gtk.gdk.Color()
        avatar_size = 48;
        max_width = 300;

        # window attributes
        self.set_border_width(10)

        # labels
        self._title = title
        markup1 = '<span foreground="%s" weight="ultrabold">%s</span>'
        titleLabel = gtk.Label(markup1 % (self.FColor, \
                               MarkupParser.escape(self._title)))
        titleLabel.set_use_markup(True)
        titleLabel.set_justify(gtk.JUSTIFY_CENTER)
        titleLabel.set_ellipsize(pango.ELLIPSIZE_END)

        self.text = text
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
        hbox = gtk.HBox()
        self.messageVbox = gtk.VBox()
        lbox = gtk.HBox()
        lbox.set_spacing(10)

        lboxEventBox = gtk.EventBox()
        lboxEventBox.set_visible_window(False)
        lboxEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        lboxEventBox.connect("button_press_event", self.onClick)
        lboxEventBox.add(lbox)
        self.connect("button_press_event", self.onClick)

        # pack everything
        self.messageVbox.pack_start(titleLabel, True, True)
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
        self.set_opacity(0.9)

        self.timerId = None
        self.set_default_size(max_width,-1)
        self.show_all()
        self.relocate()

    def append_text(self, text):
        '''
        adds text at the end of the actual text
        '''
        self.text = self.text + "\n" + text
        self.messageLabel.set_text(self.markup2 % (self.FColor, \
                                   MarkupParser.escape(self.text)))
        self.messageLabel.set_use_markup(True)
        self.messageLabel.show()
        self.relocate()

    def relocate(self):
        '''
        move notification to it's place
        '''
        width, height = self.get_size()
        # TODO: need config files for extension!
        gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.set_gravity(gravity)

        x = 0
        y = 0

        # move notification so taskbar won't hide it on Windows!
        if os.name == "nt":
            screen_w = gtk.gdk.screen_width()
            screen_h = gtk.gdk.screen_height()
            if gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                x = screen_w - width - 20
                y = screen_h - height - 10
                if taskbarSide == "bottom":
                    y = screen_h - height - taskbarSize - 10
                elif taskbarSide == "right":
                    x = screen_w - width - taskbarSize
            elif gravity == gtk.gdk.GRAVITY_NORTH_EAST:
                x = screen_w - width - 10
                y = 10
                if taskbarSide == "top":
                    y = taskbarSize
                elif taskbarSide == "right":
                    x = screen_w - width - taskbarSize
            elif gravity == gtk.gdk.GRAVITY_SOUTH_WEST:
                x = 10
                y = screen_h - height - 10
                if taskbarSide == "bottom":
                    y = screen_h - height - taskbarSize
                elif taskbarSide == "left":
                    x = taskbarSize
            elif gravity == gtk.gdk.GRAVITY_NORTH_WEST:
                x = 10
                y = 10
                if taskbarSide == "top":
                    y = taskbarSize
                elif taskbarSide == "left":
                    x = taskbarSize

        self.move(x,y)

    def onClick(self, widget, event):
        '''
        action to be done if user click's the notification
        '''
        # TODO: if the notification notifies a user going online, the click
        # should open a new conversation with that user
        self.close()

    def show(self):
        ''' show it and run the timeout'''
        self.show_all()
        self.timerId = glib.timeout_add(100000, self.close)
        return True

    def close(self , *args):
        ''' hide the Notification and show the next one'''
        global actual_notification

        self.hide()
        if self.timerId is not None:
            glib.source_remove(self.timerId)
        if len(queue) != 0:
            title, text, picturePath = queue.pop(0)
            actual_notification = Notification(title, text, picturePath)
            actual_notification.show()
        else:
            actual_notification = None
        self.destroy()
