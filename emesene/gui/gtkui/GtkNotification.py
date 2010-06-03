import gtk
import pango

import os
import logging
log = logging.getLogger('gui.gtkui.GtkNotification')

NAME = 'GtkNotification'
DESCRIPTION = 'Emesene\'s notification system\'s gtk ui'
AUTHOR = 'arielj'
WEBSITE = 'www.emesene.org'


# This code is used only on Windows to get the location on the task bar and
# move notifications away from the taskbar
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
        taskbarSide = "bottom"
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

def gtkNotification(title, text, picturePath=None):
    noti = Notification(title, text, picturePath)
    noti.show()

class Notification(gtk.Window):
    def __init__(self, title, text, picturePath):

        gtk.Window.__init__(self)

        self.set_accept_focus(False)
        self.set_decorated(False)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)

        self.callback = None

        self.set_geometry_hints(None, min_width=300, min_height=60, \
                max_width=300, max_height=60)
        self.set_border_width(10)

        messageLabel = gtk.Label(text)
#        messageLabel.set_use_markup(True)
        messageLabel.set_justify(gtk.JUSTIFY_CENTER)
        messageLabel.set_ellipsize(pango.ELLIPSIZE_END)

        hbox = gtk.HBox()
        self.messageVbox = gtk.VBox()
        lbox = gtk.HBox()
        lbox.set_spacing(10)
        titleLabel = gtk.Label(title)
#        titleLabel.set_use_markup(True)
        titleLabel.set_justify(gtk.JUSTIFY_CENTER)
        titleLabel.set_ellipsize(pango.ELLIPSIZE_END)

        avatarImage = gtk.Image()
        if picturePath != None and picturePath != "file://":
            try:
                userPixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                                                   picturePath[7:],48, 48)
                avatarImage.set_from_pixbuf(userPixbuf)
            except:
                pass

        lboxEventBox = gtk.EventBox()
        lboxEventBox.set_visible_window(False)
        lboxEventBox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
        lboxEventBox.connect("button_press_event", self.onClick)
        lboxEventBox.add(lbox)
        self.connect("button_press_event", self.onClick)

        self.messageVbox.pack_start(titleLabel,False, False)
        self.messageVbox.pack_start(messageLabel,True, True)

        lbox.pack_start(avatarImage, False, False)
        lbox.pack_start(self.messageVbox, True, True)

        hbox.pack_start(lboxEventBox, True, True)

        self.add(hbox)
        
        width, height = self.get_size()
        gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.set_gravity(gravity)

        x = 0
        y = 0

        #move notification so taskbar won't hide it on Windows!
        if os.name == "nt":
            if gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                x = gtk.gdk.screen_width() - width - 10
                y = gtk.gdk.screen_height() - height - 10
                if taskbarSide == "bottom":
                    y = gtk.gdk.screen_height() - height - taskbarSize
                elif taskbarSide == "right":
                    x = gtk.gdk.screen_width() - width - taskbarSize
            elif gravity == gtk.gdk.GRAVITY_NORTH_EAST:
                x = gtk.gdk.screen_width() - width - 10
                y = 10
                if taskbarSide == "top":
                    y = taskbarSize
                elif taskbarSide == "right":
                    x = gtk.gdk.screen_width() - width - taskbarSize
            elif gravity == gtk.gdk.GRAVITY_SOUTH_WEST:
                x = 10
                y = gtk.gdk.screen_height() - height - 10
                if taskbarSide == "bottom":
                    y = gtk.gdk.screen_height() - height - taskbarSize
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

#        #don't use a rectangular form
#        window = self.get_root_window()
#        if window is not None:
#            rect = gtk.gdk.Rectangle(1,10,10,10)
#            window.shape_combine_region(gtk.gdk.region_rectangle(rect),50,10)

#        # A bit of transparency to be less intrusive
#        self.set_opacity(0.85)

        hbox.show_all()

    def onClick(self, widget, event):
        self.close()

    def show(self):
        ''' show it '''
        self.show_all()
        return True

    def close(self , *args):
        ''' hide the Notification '''
        self.hide()
