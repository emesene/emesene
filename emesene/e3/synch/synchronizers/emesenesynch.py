# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
#
#    Module written by Andrea Stagi <stagi.andrea(at)gmail.com>

from synch import Synch
import sqlite3.dbapi2 as sqlite
from datetime import date
from time import sleep
import os
import e3
import shutil

EM1_SELECT_USER = "select * from user"
EM2_SELECT_USER = "select * from d_account"
EM1_SELECT_CONVERSATIONS = "select conversation.id,account as account1,stamp,data from user inner join conversation_event on ( user.id=conversation_event.id_user ) inner join conversation on(conversation.id=conversation_event.id_conversation) inner join event on(conversation_event.id_event=event.id)"
EM1_SELECT_DEST_USER = "select distinct account from (conversation_event inner join user on conversation_event.id_user = user.id) where conversation_event.id_conversation=%s and account <> '%s'"

LOGGER_MAXLIMIT = 500
LOGGER_MINLIMIT = 30


class EmeseneSynch(Synch):

        def __init__(self):
            Synch.__init__(self)

        def exists_source(self):
            return os.path.exists(self.__src_db_path)

        def set_user(self, user_account):

            self.__myuser = user_account

            emesene1_usr_acc = (user_account.replace("@","_")).replace(".","_")

            self.__source_path = os.path.join(os.path.expanduser("~"),".config","emesene1.0",
                                    emesene1_usr_acc)
            self.__dest_path = os.path.join(os.path.expanduser("~"),".config","emesene2",
                                  "messenger.hotmail.com",user_account)

            self.__src_db_path = os.path.join(self.__source_path, "cache",user_account + ".db")
            self.__dest_db_path = os.path.join(self.__dest_path, "log","base.db")

        def __reset_progressbar(self):
            self._prog_callback(0.0)

        def start_synch(self):
            self.__synch_my_avatars()
            self.__synch_other_avatars()
            self.__synch_conversations()

        def __synch_my_avatars(self):
            self.__reset_progressbar()
            self._action_callback(_("Importing your avatars..."))

            listing = os.listdir(os.path.join(self.__source_path, "avatars"))
            percent = e3.common.PercentDone(len(listing))
            actual_avatar = 0.0

            for infile in listing:
                shutil.copy (os.path.join(self.__source_path, "avatars", infile), 
                             os.path.join(self.__dest_path, "avatars", infile) )

                actual_avatar += 1.0

                if percent.notify(actual_avatar):
                    self._prog_callback(percent.current)

        def __synch_other_avatars(self):
            self.__reset_progressbar()
            self._action_callback(_("Importing contact avatars..."))

        def __synch_conversations(self):
            self.__reset_progressbar()
            self._action_callback(_("Importing conversations..."))

            #Get all old users

            self.__conn_src = sqlite.connect(self.__src_db_path)
            users = self.__conn_src.cursor()
            users.execute(EM1_SELECT_USER)

            self.__conn_dest = sqlite.connect(self.__dest_db_path)
            dest_users = self.__conn_dest.cursor()
            dest_users.execute(EM2_SELECT_USER)

            user_names=[]

            for dest_user in dest_users:
                user_names.append(dest_user[1])

            for user in users:

                found=0

                for dest_user in user_names:
                    if(user[1].lower() == dest_user.lower()):
                        found=1

                if found == 0:
                    new_account = self.__user_to_account(user[1])
 
                    if(new_account == None):
                        new_account = e3.base.Contact(user[1])
                        new_account = e3.Logger.Account.from_contact(new_account)
                        self._session.logger.log("status change", 0, new_account.nick, new_account)
                    else:
                        self._session.logger.log("status change", 0, new_account.nick, new_account)


            #Get all old conversations		

            conversations = self.__conn_src.cursor()

            conversations.execute(EM1_SELECT_CONVERSATIONS)

            conversations_attr=[]

            id_conv = -1
            other_users_fetched = []
            actual_conv = 0
            conversations_list = conversations.fetchall()
           
            percent = e3.common.PercentDone(len(conversations_list))

            for conv in conversations_list:

                users_fetched = []
                
                if id_conv != conv[0]:
                    other_users_fetched = self.__dest_user(conv[0])
                    id_conv = conv[0]

                if (self.__myuser != conv[1]):
                    users_fetched.append(self.__user_to_account(self.__myuser))
                else:
                    users_fetched.extend(other_users_fetched)

                actual_conv += 1.0

                if percent.notify(actual_conv):
                    self._prog_callback(percent.current)

                for user_fetched in users_fetched:
                    conversations_attr.append({"user" : self.__user_to_account(conv[1]), 
                                               "dest" : user_fetched, 
                                               "time" : conv[2], 
                                               "data" : self.__data_conversion(conv[3])})


            actual_conv = 0  
            percent = e3.common.PercentDone(len(conversations_attr))

            self.__reset_progressbar()
            self._action_callback(_("Storing conversations..."))

            for conv in conversations_attr:
                self._session.logger.log("message", 0, conv["data"], 
                                         conv["user"], conv["dest"], conv["time"])

                actual_conv += 1.0

                if percent.notify(actual_conv):
                    self._prog_callback(percent.current)

                while (self._session.logger.input_size >= LOGGER_MAXLIMIT):
                    while (self._session.logger.input_size > LOGGER_MINLIMIT):
                        sleep(1)

        def __user_to_account(self,user):

            for account in self._session.contacts.contacts.keys():
                if(account.lower() == user.lower()):
                    user = account

            founded_account = self._session.contacts.get(user)

            if(founded_account != None):
                return e3.Logger.Account.from_contact( founded_account )
            else:
                return e3.Logger.Account.from_contact( e3.base.Contact(user) )


        def __dest_user(self, conv_id):

             users = []

             users_dest = self.__conn_src.cursor()
             users_dest.execute(EM1_SELECT_DEST_USER % (conv_id,self.__myuser))

             for user_found in users_dest:
                 users.append(self.__user_to_account(user_found[0]))

             return users


        def __time_conversion(self, time):
            return date.fromtimestamp(time)


        def __data_conversion(self, data):
            d=data.partition("UTF-8\r\n")
            end=d[2].encode('UTF-8')
            return end



