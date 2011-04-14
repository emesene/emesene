'''file transfer handling module'''
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

import time

class FileTransfer(object):
    '''a class that represent a file transfer'''
    (WAITING, TRANSFERRING, RECEIVED, FAILED) = range(4)

    def __init__(self, obj, filename, contact, size, preview, sender='Me', completepath=''):
        self.filename = filename
        self.completepath = completepath
        self.size = size
        self.preview = preview

        self.object = obj
        self.contact = contact

        self.state = FileTransfer.WAITING
        self.sender = sender
        self.received_data = 0

        self.time_start = 0
        self.time_finished = 0

    def __str__(self):
        '''return a string representation of a file transfer'''
        return '<e3.base.filetransfer filename="%s" len="%i">' % (self.filename,
                                                            self.received_data)

    def get_progress(self):
        ''' returns the lenght of the received data '''
        return self.received_data

    def get_fraction(self):
        ''' received the percentage, which is < 1 and > 0 '''
        return (float(self.received_data) / self.size)

    def get_eta(self):
        ''' returns the estimated time left to finish the transfer '''
        if self.received_data:
            return ((self.size - self.received_data) / (self.get_speed() or 0.1))
        return 0    

    def get_speed(self):
        ''' returns the average speed of the transfer '''
        if self.state is FileTransfer.WAITING or self.get_time() == 0:
            return 0
        return (self.received_data / self.get_time())

    def get_time(self):
        ''' returns the elapsed time since the start of the transfer '''
        if self.state in (FileTransfer.RECEIVED, FileTransfer.FAILED):
            return (self.time_finished - self.time_start)
        elif self.received_data:
            return (time.time() - self.time_start)
        return 0
