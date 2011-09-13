# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import xml.sax.saxutils as xml

def soap_header(security_token):
    """Returns the SOAP xml header"""

    t, p = security_token.split('&')

    return """
      <PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
          <t>%s</t> 
          <p>%s</p>
      </PassportCookie>""" % (xml.escape(t[2:]), 
                              xml.escape(p[2:]))
