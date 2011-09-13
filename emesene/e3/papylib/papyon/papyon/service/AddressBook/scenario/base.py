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

from papyon.util.async import *

__all__ = ['BaseScenario', 'Scenario']

class BaseScenario(object):
    def __init__(self, partner_scenario, callback, errback):
        self._scenario = partner_scenario
        self._callback = callback
        self._errback = errback

    def __set_scenario(self, scenario):
        self._scenario = scenario
    def __get_scenario(self):
        return self._scenario
    scenario = property(__get_scenario, __set_scenario)

    def callback(self, *args):
        run(self._callback, *args)

    def errback(self, *args):
        run(self._errback, *args)

    def execute(self):
        pass

    def __call__(self):
        return self.execute()

class Scenario(object):
    """Scenario label"""

    INITIAL = "Initial"
    TIMER = "Timer"
    CONTACT_SAVE = "ContactSave"
    GROUP_SAVE = "GroupSave"
    BLOCK_UNBLOCK = "BlockUnblock"
    CONTACT_MSGR_API = "ContactMsgrAPI"
    MOBILE_CONTACT_MSGR_API = "MobileContactMsgrAPI"
    MESSENGER_PENDING_LIST = "MessengerPendingList"
