# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
from papyon.service.OfflineIM.constants import *
from papyon.service.OfflineIM.scenario.base import BaseScenario

__all__ = ['FetchMessagesScenario']

class FetchMessagesScenario(BaseScenario):
    def __init__(self, rsi, callback, errback, global_callback, message_ids=[]):
        """Accepts an invitation.

            @param rsi: the rsi service
            @param message_ids: id list of messages to fetch
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, callback, errback)
        self.__rsi = rsi
        self.__global_callback = global_callback

        self.message_ids = message_ids

    def execute(self):
        for message_id in self.message_ids:
            self.__rsi.GetMessage((self.__get_message_callback, message_id),
                                  (self.__get_message_errback,),
                                  message_id, False)

    def __get_message_callback(self, run_id, seq_num, message, id):
        callback = self._callback
        callback[0](id, run_id, seq_num, message, *callback[1:])
        self.message_ids.remove(id)
        if self.message_ids == []:
            global_callback = self.__global_callback
            global_callback[0](*global_callback[1:])

    def __get_message_errback(self, error_code):
        errcode = OfflineMessagesBoxError.UNKNOWN
        errback = self._errback[0]
        args = self._errback[1:]
        errback(errcode, *args)
