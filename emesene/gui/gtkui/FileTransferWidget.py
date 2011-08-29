''' a gtk widget for managing file transfers '''
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

import gtk
import pango
import gobject
import extension
import time

import gui

import hashlib
import tempfile

class FileTransferWidget(gtk.HBox):
    '''this class represents the ui widget for one filetransfer'''

    def __init__(self, main_transfer_bar, transfer):
        gtk.HBox.__init__(self)

        self.handler = gui.base.FileTransferHandler(main_transfer_bar.session, transfer)

        self.main_transfer_bar = main_transfer_bar
        self.transfer = transfer
        
        self.event_box = gtk.EventBox()
        self.progress = gtk.ProgressBar()
        self.progress.set_ellipsize(pango.ELLIPSIZE_END)
        self.progress.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.progress.connect('button-press-event', self._on_dbl_click_transfer)

        self.menu = gtk.Menu()

        img_file = gtk.image_new_from_stock(gtk.STOCK_FILE, \
                                        gtk.ICON_SIZE_BUTTON)
        img_dir = gtk.image_new_from_stock(gtk.STOCK_OPEN, \
                                        gtk.ICON_SIZE_BUTTON)

        m_open_file = gtk.ImageMenuItem(_('Open file'))
        m_open_file.connect('activate', self._on_menu_file_clicked)
        m_open_file.set_image(img_file)

        m_open_dir = gtk.ImageMenuItem(_('Open folder'))
        m_open_dir.connect('activate', self._on_menu_folder_clicked)
        m_open_dir.set_image(img_dir)

        self.menu.add(m_open_file)
        self.menu.add(m_open_dir)

        self.event_box.add(self.progress)
        self.pack_start(self.event_box, False, False)

        self.buttons = []
        self.show_all()
        self.tooltip = FileTransferTooltip(self.event_box, self.transfer)

        self.notifier = extension.get_default('notificationGUI')

        self.event_box.connect('event', self._on_progressbar_event)

        self.do_update_progress()
        self.on_transfer_state_changed()

    def _on_dbl_click_transfer(self, widget, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            if self.transfer.state == self.transfer.RECEIVED:
                self.handler.open()

    def _on_progressbar_event(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS:
            if self.transfer.state == self.transfer.RECEIVED:
                if event.button == 3:
                    self.menu.show_all()
                    self.menu.popup(None, None, None, event.button, event.time)

    def _on_menu_file_clicked(self, widget):
        self.handler.open()

    def _on_menu_folder_clicked(self, widget):
        self.handler.opendir()

    def accepted(self):
        ''' called when the other party accepts our transfer '''
        self.handler.accepted()

    def finished(self):
        ''' sets the transfer state to finished '''
        self.transfer.state = self.transfer.RECEIVED

    def canceled(self):
        ''' sets the transfer state to canceled '''
        self.transfer.state = self.transfer.CANCELED
        
    def do_update_progress(self):
        ''' updates the progress bar status '''
        if self.transfer.state == self.transfer.RECEIVED:
            self.progress.set_fraction(1)  # 100%
        else:
            self.progress.set_fraction(self.transfer.get_fraction())
        self.progress.set_text(self.transfer.filename)
        self.tooltip.update()
        self.on_transfer_state_changed()

    def on_transfer_state_changed(self):
        ''' when the transfer changes its state '''
        state = self.transfer.state

        # remove existing buttons
        for button in self.buttons:
            self.remove(button)

        self.buttons = []

        if state == self.transfer.WAITING and self.transfer.sender != 'Me':
            button = gtk.Button(None, None)
            button.set_tooltip_text(_('Accept transfer'))            
            button.set_image(self.__get_button_img(gtk.STOCK_APPLY))
            button.connect('clicked', self._on_accept_clicked)
            self.buttons.append(button)

        if state == self.transfer.WAITING or state == self.transfer.TRANSFERRING:
            b_cancel = gtk.Button(None, None)
            if state == self.transfer.WAITING and self.transfer.sender != 'Me':
                b_cancel.set_tooltip_text(_('Reject transfer'))
            else:
                b_cancel.set_tooltip_text(_('Cancel transfer'))
            b_cancel.set_image(self.__get_button_img(gtk.STOCK_CANCEL))
            b_cancel.connect('clicked', self._on_cancel_clicked)
            self.buttons.append(b_cancel)

        if state in (self.transfer.RECEIVED, self.transfer.FAILED):
            self.transfer.time_finished = time.time()

            button = gtk.Button(None, None)
            button.set_tooltip_text(_('Close transfer'))
            button.set_image(self.__get_button_img(gtk.STOCK_CLEAR))
            button.connect('clicked', self._on_close_clicked)
            self.buttons.append(button)

        if state == self.transfer.CANCELED:
            self._on_close_clicked(None)

        for button in self.buttons:
            self.pack_start(button, False, False)

        self.show_all()
        #self.do_update_progress()

    def __get_button_img(self, stock_img):
        ''' returns a gtk image '''
        img = gtk.Image()
        img.set_from_stock(stock_img, gtk.ICON_SIZE_MENU)
        return img

    def _on_cancel_clicked(self, widget):
        self.handler.cancel()
        self.main_transfer_bar.hbox.remove(self)
        self.main_transfer_bar.num_transfers -= 1
        if self.main_transfer_bar.num_transfers == 0:
            self.main_transfer_bar.hide()

    def _on_accept_clicked(self, widget):
        self.handler.accept()

    def _on_close_clicked(self, widget):
        self.main_transfer_bar.hbox.remove(self)
        self.main_transfer_bar.num_transfers -= 1
        if self.main_transfer_bar.num_transfers == 0:
            self.main_transfer_bar.hide()

DELAY = 500

class FileTransferTooltip(gtk.Window):
    '''Class that implements the filetransfer tooltip'''
    def __init__(self, w_parent, transfer):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)

        self.transfer = transfer

        self.set_name('gtk-tooltips')
        self.set_position(gtk.WIN_POS_MOUSE)
        self.set_resizable(False)
        self.set_border_width(4)
        self.set_app_paintable(True)

        self.image = gtk.Image()
        self.details = gtk.Label()
        self.details.set_alignment(0, 0)

        self.table = gtk.Table(3, 2, False)
        self.table.set_col_spacings(5)

        self.add_label(_('Status:'), 0, 1, 0, 1)
        self.add_label(_('Average speed:'), 0, 1, 1, 2)
        self.add_label(_('Time elapsed:'), 0, 1, 2, 3)
        self.add_label(_('Estimated time left:'), 0, 1, 3, 4)

        self.status = gtk.Label()
        self.speed = gtk.Label()
        self.elapsed = gtk.Label()
        self.etl = gtk.Label()

        self.add_label('', 1, 2, 0, 1, self.status)
        self.add_label('', 1, 2, 1, 2, self.speed)
        self.add_label('', 1, 2, 2, 3, self.elapsed)
        self.add_label('', 1, 2, 3, 4, self.etl)

        vbox = gtk.VBox(False, 5)
        vbox.pack_start(self.details, False, False)
        vbox.pack_start(self.table, False, False)

        hbox = gtk.HBox(False, 5)
        hbox.pack_start(self.image, False, False)
        hbox.pack_start(vbox, True, True)

        self.add(hbox)

        self.connect('expose-event', self.on_expose_event)
        w_parent.connect('enter-notify-event', self.on_motion)
        w_parent.connect('leave-notify-event', self.on_leave)

        self.pointer_is_over_widget = False

        self.__fileprev=None

    def add_label(self, l_string, left, right, top, bottom, label = None):
        ''' adds a label to the widget '''
        if label == None:
            label = gtk.Label(l_string)

        label.set_alignment(0, 0)
        self.table.attach(label, left, right, top, bottom)

    def on_motion(self, view, event):
        ''' called when the cursor is on the widget '''
        self.pointer_is_over_widget = True
        eventCoords = (event.x_root, event.y_root, int(event.y))
        gobject.timeout_add(DELAY, self.show_tooltip, \
                                            view, eventCoords)

    def show_tooltip(self, view, o_coords):
        ''' shows the tooltip with the transfer's informations '''
        # tooltip is shown after a delay, so we have to check
        # if mouse is still over parent widget
        if not self.pointer_is_over_widget:
            return

        if self.transfer.preview is not None:
            if(self.__fileprev==None):
                self.__fileprev=tempfile.mkstemp(prefix=hashlib.md5(self.transfer.preview).hexdigest(), 
                                                 suffix=hashlib.md5(self.transfer.preview).hexdigest())[1]

            tmpPrev = open( self.__fileprev, 'wb' )
            tmpPrev.write(self.transfer.preview)
            tmpPrev.close()

            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(self.__fileprev)
            except:
                pixbuf = gtk.gdk.pixbuf_new_from_file(gui.theme.image_theme.transfer_success) #sometime happens -.-
        else:
            pixbuf = gtk.gdk.pixbuf_new_from_file(gui.theme.image_theme.transfer_success)
        #amsn sends a big. black preview? :S
        if pixbuf:
            if pixbuf.get_height() <= 96 and pixbuf.get_width() <= 96:
                self.image.set_from_pixbuf(pixbuf)
            else:
                pixbuf.scale_simple(96, 96, gtk.gdk.INTERP_BILINEAR)
                self.image.set_from_pixbuf(pixbuf)

        # set the location of the tooltip
        x, y = self.find_position(o_coords, view.window)
        self.move(x, y)
        self.update()
        self.show_all()
        return False

    def update(self):
        ''' updates the tooltip '''
        self.details.set_markup('<b>' + self.transfer.filename + '</b>')
        time_left = self.transfer.get_eta()
        bps = self.transfer.get_speed()
        seconds = self.transfer.get_time()
        
        percentage = int(self.transfer.get_fraction() * 100)
        self.status.set_text('%d%% (%d/%d KB)' % (percentage, \
            int(self.transfer.received_data)/1024, int(self.transfer.size) / 1024))
        self.elapsed.set_text('%.2d:%.2d' % (int(seconds / 60), \
            int(seconds % 60)))
        self.speed.set_text('%.2f KiB/s' % (float(bps) / 1024.0))
        self.etl.set_text('%.2d:%.2d' % (int(time_left / 60), \
            int(time_left % 60)))

    def on_leave(self, view, event):
        ''' called when the pointer leaves the widget '''
        self.pointer_is_over_widget = False
        self.hide()

    # display a border around the tooltip
    def on_expose_event(self, tooltip_window, event):
        ''' called when the widget is going to be exposed '''
        width, height = tooltip_window.get_size()
        tooltip_window.style.paint_flat_box(tooltip_window.window, \
                                            gtk.STATE_NORMAL, gtk.SHADOW_OUT, \
                                            None, tooltip_window, 'tooltip', \
                                            0, 0, width, height)

    def find_position(self, o_coords, view_win):
        ''' finds the correct position '''
        x_root, y_root, origY = o_coords
        currentY = view_win.get_pointer()[1]

        width, height = self.get_size()
        s_width, s_height = gtk.gdk.screen_width(), gtk.gdk.screen_height()

        x = int(x_root) - width/2
        if currentY >= origY:
            y = int(y_root) + 24
        else:
            y = int(y_root) + 6

        # check if over the screen
        if x + width > s_width:
            x = s_width - width
        elif x < 0:
            x = 0

        if y + height > s_height:
            y = y - height - 24
        elif y < 0:
            y = 0

        return (x, y)
