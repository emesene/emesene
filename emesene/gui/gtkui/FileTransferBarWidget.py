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
import gobject

import e3.base
import extension

class FileTransferBarWidget(gtk.HBox):
    '''bar which represents active file transfers'''
    def __init__(self, session):
        gtk.HBox.__init__(self)

        self.session = session
        self.ft = extension.get_default('filetransfer widget')

        self.set_spacing(3)

        self.hbox = gtk.HBox()
        self.hbox.set_spacing(3)

        self.layout = gtk.Layout()
        self.layout.put(self.hbox, 0, 0)
        self.layout.set_size(self.hbox.get_allocation().width, \
                               self.hbox.get_allocation().height + 100)

        self.current = 0
        self.speed = 5
        self.page = 0
        self.twidth = 150
        self.num_transfers = 0
        self.dest = 0
        self.div = 0
        self.new_transfer_bar = None
        self.transfers = {}

        arrow_left = gtk.Arrow(gtk.ARROW_LEFT, gtk.SHADOW_IN)
        arrow_right = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_IN)
        self.b_go_left = gtk.Button()
        self.b_go_left.add(arrow_left)
        self.b_go_left.set_sensitive(False)
        self.b_go_left.set_relief(gtk.RELIEF_NONE)
        self.b_go_left.connect('clicked', self._on_left_button_clicked)

        self.b_go_right = gtk.Button()
        self.b_go_right.add(arrow_right)
        self.b_go_right.set_sensitive(False)
        self.b_go_right.set_relief(gtk.RELIEF_NONE)
        self.b_go_right.connect('clicked', self._on_right_button_clicked)

        self.pack_start(self.b_go_left, False, False)
        self.pack_start(self.layout)
        self.pack_start(self.b_go_right, False, False)


    def add(self, transfer):
        ''' add a new transfer to the widget '''
        self.new_transfer_bar = self.ft(self, transfer)
        # add to e3.base transfer : gui/gtk transfer dict
        self.transfers[transfer] = self.new_transfer_bar
        self.hbox.pack_start(self.new_transfer_bar, False, False)
        self.num_transfers += 1
        if self.num_transfers > 1:
            self.b_go_right.set_sensitive(True)
        else:
            self.b_go_right.set_sensitive(False)
        self.set_no_show_all(False)
        self.show_all()

    def update(self, transfer):
        ''' called when the bar needs to be updated '''
        tr = self.transfers[transfer]
        tr.do_update_progress()

    def finished(self, transfer):
        ''' called when the bar needs to be updated '''
        tr = self.transfers[transfer]
        tr.finished()
        tr.do_update_progress()

    def _on_left_button_clicked(self, widget):
        ''' when the user click on the go-left button '''
        self.twidth = self.new_transfer_bar.get_allocation().width
        self.page -= 1
        self.dest = -self.twidth * self.page
        gobject.timeout_add(5, self._move_to_left)

    def _on_right_button_clicked(self, widget):
        ''' when the user click on the go-right button '''
        if self.num_transfers == 1: 
            self.b_go_right.set_sensitive(False)
            return False
        self.twidth = self.new_transfer_bar.get_allocation().width
        self.b_go_left.set_sensitive(True)
        self.page += 1
        self.dest = -self.twidth * self.page
        gobject.timeout_add(5, self._move_to_right)

    def _move_to_right(self, *args):
        ''' moves the widgets on the right smoothly '''
        self.div = self.num_transfers - 1

        if self.dest == (self.dest * self.page) / self.div:
            self.b_go_right.set_sensitive(False)

        if self.current > self.dest:
            self.current -= self.speed
            self.layout.move(self.hbox, self.current, 0)
            return True
        return False

    def _move_to_left(self, *args):
        ''' moves the widgets on the left smoothly '''
        if self.dest == 0: 
            self.b_go_left.set_sensitive(False)
        if self.dest >= 0:
            self.b_go_right.set_sensitive(True)
                
        if self.current < self.dest:
            self.current += self.speed
            self.layout.move(self.hbox, self.current, 0)
            return True
        return False

