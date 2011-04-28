'''module to define a class to handle a call'''
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

import gui

class CallWindow(gtk.Window):
    '''A dialog to choose an avatar'''

    def __init__(self, session):
        '''Constructor, response_cb receive the response number, the new file
        selected and a list of the paths on the icon view.
        picture_path is the path of the current display picture,
        '''
        gtk.Window.__init__(self)
        self.set_default_size(320, 520)
        self.set_border_width(4)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.connect("delete_event", self.delete_event)

        vbox = gtk.VBox()
        self.add(vbox)
        self.movie_window_other = gtk.DrawingArea()
        self.movie_window_self = gtk.DrawingArea()
        developer_ads = gtk.Label("If you want to send your audio/video, just fix emesene/e3/papylib/PapyConference.py and add a nice gui to it.")
        developer_ads.set_line_wrap(True)
        vbox.pack_start(developer_ads, False)
        vbox.pack_start(self.movie_window_other)
        vbox.pack_start(self.movie_window_self)
        hbox = gtk.HBox()
        vbox.pack_start(hbox, False)
        hbox.set_border_width(10)
        fortune_label = gtk.Label()
        fortune_label.set_markup("<i>..and then thee'll have audio/video calls,\n  but thou shalt not annoy thy developers.\n    --c10ud, the book of emesene 2:11-5</i>")
        hbox.pack_start(fortune_label)
        self.btn_accept = gtk.Button(_("Accept call"))
        self.btn_accept.connect("clicked", self.accept_call)
        hbox.pack_start(self.btn_accept, False)
        self.btn_cancel = gtk.Button(_("Cancel call"))
        self.btn_cancel.connect("clicked", self.cancel_call)
        hbox.pack_start(self.btn_cancel, False)
        self.btn_reject = gtk.Button(_("Reject call"))
        self.btn_reject.connect("clicked", self.reject_call)
        hbox.pack_start(self.btn_reject, False)
        hbox.add(gtk.Label())

        self.session = session
        self.handler = None
        self.westart = False

    def add_call(self, call, westart):
        ''' adds an e3.Call to the widget'''
        self.westart = westart
        self.call = call
        self.set_title(_("Call Manager") + " - %s" % self.call.peer)
        self.handler = gui.base.CallHandler(self.session, call)

    def accept_call(self, *args):
        ''' set the xids and accept the call'''
        if self.handler:
            self.handler.accept()
            self.btn_accept.hide()
            self.btn_reject.hide()

    def reject_call(self, *args):
        ''' rejects a call '''
        if self.handler:
            self.handler.reject()
        self.handler = None
        self.hide()

    def cancel_call(self, *args):
        ''' cancels a call '''
        if self.handler:
            self.handler.cancel()
        self.handler = None
        self.hide()

    def set_xids(self):
        '''sets the call variables to our window's drawingarea xids'''
        self.call.surface_buddy = self.movie_window_other.window.xid
        self.call.surface_self = self.movie_window_self.window.xid

    def get_xids(self):
        ''' returns a tuple with two XIDs '''
        return (self.movie_window_other.window.xid, self.movie_window_self.window.xid)

    def show_all_widgets(self):
        ''' takes care of showing the correct widgets '''
        self.show_all()
        if self.westart:
            self.btn_accept.hide()
            self.btn_reject.hide()

    def delete_event(self, widget, event, data=None):
        ''' cancels any call that might be in progress, then hide '''
        self.cancel_call()
        self.hide()
        return True
