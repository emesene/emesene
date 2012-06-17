'''This module provides a dummy external implementation API for emesene'''
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

import logging
log = logging.getLogger("emesene.e3.common.DBus")
import extension

class DummyExternalAPI(object):
    provides=('external api', )
    def set_new_session(self, session, window):
        pass

extension.register('external api', DummyExternalAPI)
extension.set_default('external api', DummyExternalAPI)
