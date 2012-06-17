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
"""Dummy Implementation of a Network Manager."""

import logging
log = logging.getLogger("emesene.e3.common.NetworkManagerHelper")
import extension

class DummyNetworkChecker():
    ''' this class does lazy checks for network availability and 
    disconnects emesene if the network goes down '''

    #Public methods
    def set_new_session(self, session):
        pass

    def stop(self):
        pass

extension.category_register('network checker', DummyNetworkChecker)
extension.set_default('network checker', DummyNetworkChecker)
