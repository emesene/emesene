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
from papyon.msnp.challenge import _msn_challenge

__all__ = ['SendMessageScenario']

class SendMessageScenario(BaseScenario):
    def __init__(self, oim, client, recipient, message, callback, errback):
        """Accepts an invitation.

            @param oim: the oim service
            @param client: the client object sending the OIM
            @param recipient: the contact to send the OIM to
            @param message: the message to send
            @param callback: tuple(callable, *args)
            @param errback: tuple(callable, *args)
        """
        BaseScenario.__init__(self, callback, errback)
        self.__oim = oim
        self.__client = client
        self.__from = client.profile
        self.__to = recipient
        
        self.run_id = ""
        self.sequence_num = -1

        self.__msg = message

    def execute(self):
        self.__oim.Store2((self.__store2_callback,),
                          (self.__store2_errback,), 
                          self.__from.account,
                          self.__from.display_name,
                          self.__to.account,
                          self.run_id,
                          self.sequence_num,
                          "text",
                          self.__msg)
            
    def __store2_callback(self):
        callback = self._callback
        callback[0](*callback[1:])

    def __store2_errback(self, error_code,  auth_policy, lock_key_challenge):
        if error_code == OfflineMessagesBoxError.AUTHENTICATION_FAILED:
            if lock_key_challenge != None:
                self.__oim.set_lock_key(_msn_challenge(lock_key_challenge))
            if auth_policy != None:
                self._client._sso.DiscardSecurityTokens([LiveService.CONTACTS])
                self._client._sso.RequestMultipleSecurityTokens((self.execute, ), None, LiveService.CONTACTS)
                return

            self.execute()
            return

        errback = self._errback
        errback[0](error_code, *errback[1:])
