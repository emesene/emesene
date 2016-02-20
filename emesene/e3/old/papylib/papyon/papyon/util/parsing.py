# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
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

from papyon.errors import ParseError

import uuid

def parse_account(account):
    """Parse account string and extract end-point info if available."""
    account = account.lower() # normalize account
    guid = None

    if ';' in account:
        account, guid = account.split(';', 1)
        try:
            guid = uuid.UUID(guid)
        except:
            raise ParseError("Account", "invalid machine GUID", guid)

    if not '@' in account:
        raise ParseError("Account", "invalid email address", account)

    return account, guid

def build_account(account, guid):
    if not guid:
        return str(account)
    return "%s;{%s}" % (account, guid)
