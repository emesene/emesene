import gui
import utils
import gobject

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

def gtkNotification(title, text, picturePath=None):
    noti = Notification(title, text, picturePath)
    noti.show()

class Notification(gtk.Window):
    def __init__(self, title, text, picturePath):

        gtk.Window.__init__(self, type=gtk.WINDOW_POPUP)

        # constants
        FColor = "white"
        BColor = gtk.gdk.Color()
        avatar_size = 48;
        width = 300;

        # window attributes
        #self.set_accept_focus(False)
        #self.set_focus_on_map(True)
        #self.set_decorated(False)
        # self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        self.set_geometry_hints(None, min_width=width, min_height=60, \
                max_width=width, max_height=200)
        self.set_border_width(10)

        # self.set_transient_for(gtk.gdk.get_default_root_window())

        # labels
        markup1 = '<span foreground="%s" weight="ultrabold">%s</span>'
        titleLabel = gtk.Label( markup1 % (FColor, title))
        titleLabel.set_use_markup(True)
        titleLabel.set_justify(gtk.JUSTIFY_CENTER)
        titleLabel.set_ellipsize(pango.ELLIPSIZE_END)

        markup2 = '<span foreground="%s">%s</span>'
        messageLabel = gtk.Label( markup2 % (FColor, text))
        messageLabel.set_use_markup(True)
        messageLabel.set_justify(gtk.JUSTIFY_CENTER)
        messageLabel.set_ellipsize(pango.ELLIPSIZE_END)

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
        self.messageVbox.pack_start(titleLabel,False, False)
        self.messageVbox.pack_start(messageLabel,True, True)
        lbox.pack_start(avatarImage, False, False)
        lbox.pack_start(self.messageVbox, True, True)
        hbox.pack_start(lboxEventBox, True, True)

        self.add(hbox)

        # change background color
        self.set_app_paintable(True)
        self.realize()
        self.window.set_background(BColor)

#        # don't use a rectangular form, just testing some things, doesn't work
#        window = self.get_parent_window()
#        if window is not None:
#            print "entra al if"
#            rect = gtk.gdk.Rectangle(10,10,10,10)
#            window.shape_combine_region(gtk.gdk.region_rectangle(rect),50,10)

        # A bit of transparency to be less intrusive
        self.set_opacity(0.9)

        # move notification
        width, height = self.get_size()
        gravity = gtk.gdk.GRAVITY_SOUTH_EAST # can I use some configuration?
        self.set_gravity(gravity)

        x = 0
        y = 0

        # move notification so taskbar won't hide it on Windows!
        if os.name == "nt":
            screen_w = gtk.gdk.screen_width()
            screen_h = gtk.gdk.screen_height()
            if gravity == gtk.gdk.GRAVITY_SOUTH_EAST:
                x = screen_w - width - 10
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

        #self.window.set_skip_taskbar_hint(True)
        #self.window.set_skip_pager_hint(True)
        #self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
        #self.set_keep_above(True)

        self.timerId = None

        hbox.show_all()

    def onClick(self, widget, event):
        self.close()

    def show(self):
        ''' show it '''
        self.show_all()
        self.timerId = gobject.timeout_add(10000, self.close)
        return True

    def close(self , *args):
        ''' hide the Notification '''
        self.hide()
        if self.timerId is not None:
            gobject.source_remove(self.timerId)
