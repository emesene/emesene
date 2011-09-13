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

from papyon.sip.extensions.base import SIPExtension

class MSConversationIDExtension(SIPExtension):

    def __init__(self, client, core):
        SIPExtension.__init__(self, client, core)

    def extend_request(self, message):
        call = self._client.call_manager.find_call(message)
        if call is not None and call.media_session.has_video:
            conversation_id = 1
        else:
            conversation_id = 0
        message.add_header("Ms-Conversation-ID", "f=%s" % conversation_id)
