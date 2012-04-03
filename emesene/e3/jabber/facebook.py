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


import e3
import os
from pyfb.pyfb import Pyfb, PyfbException, OAuthException

import logging
log = logging.getLogger('jabber.facebook')

API_KEY = "302582423085987"
SECRET_KEY = "a36182c056595e7d5007c9f85e3ee6bc"
REDIRECT_URL = "http://emesene.github.com/emesene/index.html"

class FacebookCLient(object):

    def __init__(self, session, token):
        self._session = session
        self._session.config.get_or_set('b_fb_mail_check', True)
        self._session.config.get_or_set('b_fb_status_download', False)
        self._session.config.get_or_set('b_fb_status_write', False)
        self._session.config.get_or_set('b_fb_picture_download', False)
        self._client = Pyfb(API_KEY)
        self.active = False
        self._nick = None
        self._avatar_cache = None
        self._avatar_path = None
        # only ask for access token if we didn't have one
        if token is None:
            self.request_permitions()
        else:
            #reuse old token
            self.set_token(token, True)

    def request_permitions(self):
        '''ask user to grant access to facebook APIs'''
        if os.name == 'mac':
            #Mac didn't have webkit suppport so open link in browser
            # and ask user to copy the url
            self._client.authenticate()
            # None means fallback to non webkit dialog
            conn_url = None
        else:
            conn_url = self._client.get_auth_url(REDIRECT_URL)
        self._session.social_request(conn_url)

    def set_token(self, token, active):
        '''Set the authentication token'''
        self.active = active
        if self.active and not token is None:
            self._client.set_access_token(token)
            self.active = True

    def _get_personal_nick(self):
        '''get the person name as nick'''
        if self.active and self._nick is None:
            try:
                me = self._client.get_myself()
                self._nick = me.name
            except OAuthException:
                self.request_permitions()
            except PyfbException, ex:
                log.warn("couldn't get nick " + str(ex))

        return self._nick

    nick = property(fget=_get_personal_nick, fset=None)

    def _set_personal_message(self, message):
        '''publish a message into your wall'''
        if self.active and len(message)!= 0:
            try:
                self._client.publish(message, "me")
            except OAuthException:
                self.request_permitions()
            except PyfbException, ex:
                log.warn("couldn't publish message " + str(ex))

    def _get_personal_message(self):
        '''gets last message published into your wall'''
        message = ""
        if self.active:
            try:
                messages = self._client.get_statuses("me")
                if len(messages) > 0:
                    message = self._client.get_statuses("me", 1)[0].message
            except OAuthException:
                self.request_permitions()
            except PyfbException, ex:
                log.warn("couldn't get message " + str(ex))
        return message

    message = property(fget=_get_personal_message, fset=_set_personal_message)

    def get_unread_mail_count(self):
        '''get current unread mail count'''
        unread_count = 0
        if self.active:
            try:
                qry = self._client.fql_query("SELECT unread_count FROM mailbox_folder WHERE folder_id = 0 and viewer_id = me()")
                unread_count = qry[0].unread_count
            except OAuthException:
                self.request_permitions()
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
            query_message = self._client.fql_query("SELECT body, author_id FROM message %s" % orclause)
            query_user = self._client.fql_query("SELECT name FROM user WHERE uid =  %s" % query_message[0].author_id)
            return (query_user[0].name, query_message[0].body)
        except OAuthException:
            self.request_permitions()
        except PyfbException:
            #we don't have any unread msg
            return None

    def _get_profile_pic(self):
        '''get current profile picture'''
        path = None
        if self.active:
            try:
                avatar_url = self._client.fql_query("SELECT pic_big FROM user WHERE uid = me()")[0].pic_big
                #check if avatar url change since last time
                if not avatar_url == self._session.config.avatar_url:
                    if self._avatar_cache is None:
                        caches = e3.cache.CacheManager(self._session.config_dir.base_dir)
                        self._avatar_cache = caches.get_avatar_cache(self._session.account.account)
                    new_path = self._avatar_cache.insert_url(avatar_url)[1]
                    self._avatar_path = os.path.join(self._avatar_cache.path, new_path)
                    self._session.config.avatar_url = avatar_url
                path = self._avatar_path
            except OAuthException:
                self.request_permitions()
            except PyfbException:
                #we don't have any avatar pic
                pass

        return path

    picture = property(fget=_get_profile_pic, fset=None)

    def process_facebook_integration(self):
        '''Do social stuff'''
        if self.active:
            if self._session.config.b_fb_status_download:
                msg = self.message
                nick = self.nick
                if not (msg == self._session.contacts.me.message or \
                        nick == self._session.contacts.me.nick):
                    self._session.contacts.me.message = msg
                    self._session.contacts.me.nick = nick
                    self._session.profile_get_succeed(nick, msg)
            if self._session.config.b_fb_picture_download:
                avatar_path = self.picture
                if not (avatar_path is None or self._session.contacts.me.picture == avatar_path):
                    self._session.contacts.me.picture = avatar_path
                    self._session.picture_change_succeed(self._session.account.account, avatar_path)
