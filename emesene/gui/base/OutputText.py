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

import e3


class OutputText(object):
    '''Base class to display conversation messages'''

    def __init__(self, config):
        '''constructor'''
        self.config = config
        self.locked = 0
        self.pending = []

    def lock(self):
        '''lock the output, appended messages will be queued until
        the output is unlocked'''
        self.locked += 1

    def unlock(self):
        '''add queued messages and then unlock the output'''
        self.locked -= 1
        if self.locked <= 0:
            for msg in self.pending:
                self.add_message(msg, self.config.b_allow_auto_scroll)
            self.pending = []
            self.locked = 0

    def search_text(text, prev=False):
        ''' initiate a text search '''
        raise NotImplementedError

    def clear(self, source="", target="", target_display="",
            source_img="", target_img=""):
        '''clear the content'''
        self.pending = []

    def send_message(self, msg):
        '''add a message to the widget'''
        self.append(msg)

    def receive_message(self, msg):
        '''add a message to the widget'''
        self.append(msg)

    def information(self, msg):
        '''add an information message to the widget'''
        self.append(msg)

    def append(self, msg):
        '''appends a msg into the view'''
        if self.locked and msg.type != e3.Message.TYPE_OLDMSG:
            self.pending.append(msg)
        else:
            self.add_message(msg, self.config.b_allow_auto_scroll)

    def add_message(self, msg, scroll):
        '''add the message to the output'''
        raise NotImplementedError

    def update_p2p(self, account, _type, *what):
        ''' new p2p data has been received (custom emoticons) '''
        raise NotImplementedError

