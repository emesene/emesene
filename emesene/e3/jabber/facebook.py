# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Emesene
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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


from pyfb.pyfb import Pyfb, PyfbException

import logging
log = logging.getLogger('jabber.facebook')

API_KEY = "302582423085987"
SECRET_KEY = "a36182c056595e7d5007c9f85e3ee6bc"
REDIRECT_URL = "http://toworktogether.eu/emesenefb.html"

class FacebookCLient(object):

    def __init__(self, session):
        self._session = session
        self._client = Pyfb(API_KEY)
        self._activated = False

    def request_permitions(self):
        conn_url = self._client.get_auth_url(REDIRECT_URL)
        self._session.social_request(conn_url)

    def set_token(self, token, active):
        '''Sets the authentication token'''
        self._activated = active
        if self._activated and not token is None:
            self._client.set_access_token(token)
            self._activated = True

    def _get_personal_nick(self):
        nick = ""
        if self._activated:
            try:
                me = self._client.get_myself()
                nick = me.name
            except PyfbException, ex:
                log.warn("couldn't get nick " + str(ex))

        return nick

    nick = property(fget=_get_personal_nick, fset=None)

    def _set_personal_message(self, message):
        '''publish a message into your wall'''
        #FIXME: we need a preference about this
        if self._activated and len(message)!= 0:
            try:
                self._client.publish(message, "me")
            except PyfbException, ex:
                log.warn("couldn't publish message " + str(ex))

    def _get_personal_message(self):
        '''gets last message published into your wall'''
        message = ""
        if self._activated:
            try:
                messages = self._client.get_statuses("me")
                if len(messages) > 0:
                    message = self._client.get_statuses("me")[0].message
            except PyfbException, ex:
                log.warn("couldn't get message " + str(ex))
        return message

    message = property(fget=_get_personal_message, fset=_set_personal_message)

    def get_unread_mail_count(self):
        '''get current unread mail count'''
        unread_count = 0
        if self._activated:
            try:
                qry = self._client.fql_query("SELECT unread_count FROM mailbox_folder WHERE folder_id = 0 and viewer_id = me()")
                unread_count = qry[0].unread_count
            except PyfbException, ex:
                log.warn("couldn't get unread messages count " + str(ex))

        return unread_count

    def get_new_mail_info(self):
        '''return a tuple with sendername,message_body corresponding to the lastest unread message'''
        try:
            query_thread = self._client.fql_query("SELECT thread_id FROM thread WHERE folder_id = 0 and unread = 1")
            orclause = "WHERE "
            for thread in query_thread:
                orclause = "%s thread_id = %s OR " % (orclause, thread.thread_id)
            #strip last 'OR '
            orclause = orclause[0:len(orclause)-3]
            orclause = "%s ORDER BY created_time DESC" % orclause
            query_message = self._client.fql_query("SELECT body, author_id, created_time FROM message %s" % orclause)
            query_user = self._client.fql_query("SELECT name FROM user WHERE uid =  %s" % query_message[0].author_id)
            return (query_user[0].name, query_message[0].body)
        except PyfbException:
            #we don't have any unread msg
            return None

