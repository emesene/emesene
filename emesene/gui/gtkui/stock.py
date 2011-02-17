'''a module that map the abstract.stock module to gtk'''
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

from gui.base.stock import *

MAP = {}
MAP[ACCEPT] = gtk.STOCK_OK
MAP[ADD] = gtk.STOCK_ADD
MAP[APPLY] = gtk.STOCK_APPLY
MAP[BACK] = gtk.STOCK_GO_BACK
MAP[BOLD] = gtk.STOCK_BOLD
MAP[CANCEL] = gtk.STOCK_CANCEL
MAP[CLEAR] = gtk.STOCK_CLEAR
MAP[CLOSE] = gtk.STOCK_CLOSE
MAP[CONNECT] = gtk.STOCK_CONNECT
MAP[DELETE] = gtk.STOCK_DELETE
MAP[DISCONNECT] = gtk.STOCK_DISCONNECT
MAP[DOWN] = gtk.STOCK_GO_DOWN
MAP[EDIT] = gtk.STOCK_EDIT
MAP[ERROR] = gtk.STOCK_DIALOG_ERROR
MAP[FORWARD] = gtk.STOCK_GO_FORWARD
MAP[INFORMATION] = gtk.STOCK_DIALOG_INFO
MAP[ITALIC] = gtk.STOCK_ITALIC
MAP[NEW] = gtk.STOCK_NEW
MAP[NO] = gtk.STOCK_NO
MAP[OK] = gtk.STOCK_OK
MAP[OPEN] = gtk.STOCK_OPEN
MAP[PREFERENCES] = gtk.STOCK_PREFERENCES
MAP[PROPERTIES] = gtk.STOCK_PROPERTIES
MAP[QUESTION] = gtk.STOCK_DIALOG_QUESTION
MAP[QUIT] = gtk.STOCK_QUIT
MAP[REFRESH] = gtk.STOCK_REFRESH
MAP[REMOVE] = gtk.STOCK_REMOVE
MAP[SAVE] = gtk.STOCK_SAVE
MAP[SELECT_COLOR] = gtk.STOCK_SELECT_COLOR
MAP[SELECT_FONT] = gtk.STOCK_SELECT_FONT
MAP[STOP] = gtk.STOCK_STOP
MAP[STRIKE] = gtk.STOCK_STRIKETHROUGH
MAP[UNDERLINE] = gtk.STOCK_UNDERLINE
MAP[UP] = gtk.STOCK_GO_UP
MAP[WARNING] = gtk.STOCK_DIALOG_WARNING
MAP[YES] = gtk.STOCK_YES
MAP[ABOUT] = gtk.STOCK_ABOUT
MAP[COPY] = gtk.STOCK_COPY

def map_stock(stock_id, default=None):
    '''try to return a gtk.STOCK_ from the given stock_id
    if not found, return default'''

    if stock_id in MAP:
        return MAP[stock_id]

    return default
