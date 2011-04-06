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

from synch import synch
import sqlite3.dbapi2 as sqlite
from datetime import date
import os
import e3

EM1_SELECT_USER = "select * from user"
EM2_SELECT_USER = "select * from d_account"
EM1_SELECT_CONVERSATIONS = "select conversation.id,account as account1,stamp,data from user inner join conversation_event on ( user.id=conversation_event.id_user ) inner join conversation on(conversation.id=conversation_event.id_conversation) inner join event on(conversation_event.id_event=event.id)"
EM1_SELECT_DEST_USER = "select distinct account from (conversation_event inner join user on conversation_event.id_user = user.id) where conversation_event.id_conversation=%s and account <> '%s'"

class emesenesynch(synch):

        def __init__(self):
                synch.__init__(self)

        def exists_source(self):
            return os.path.exists(self.src_path)

        def set_user(self, user_account):

            self.__myuser = user_account

            emesene1_usr_acc = (user_account.replace("@","_")).replace(".","_")

            sourcedb = os.path.join(os.path.expanduser("~"),".config","emesene1.0",
                                    emesene1_usr_acc,"cache",user_account + ".db")
            destdb = os.path.join(os.path.expanduser("~"),".config","emesene2",
                                  "messenger.hotmail.com",user_account,"log","base.db")

            self.set_source_path(sourcedb)
            self.set_destination_path(destdb)

        def _start_synch(self):

            #Get all old users

            self.__conn_src = sqlite.connect(self.src_path)
            users = self.__conn_src.cursor()
            users.execute(EM1_SELECT_USER)

            self.__conn_dest = sqlite.connect(self.dest_path)
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
            total_conv = len(conversations_list)

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

                self._prog_callback( (actual_conv/total_conv) * 100.0 )

                for user_fetched in users_fetched:
                    conversations_attr.append({"user" : self.__user_to_account(conv[1]), 
                                               "dest" : user_fetched, 
                                               "time" : conv[2], 
                                               "data" : self.__data_conversion(conv[3])})

            """
            for conv in conversations_attr:
                print "-------------"
                print conv["user"],
                print conv["dest"],
                print conv["data"],
                print conv["time"],
                print "-------------"
                #add the event in this form :: EVENT message 0 TEXT_OF_MESSAGE <account 'mail1'> <account 'mail2'> time
             """

            for conv in conversations_attr:
                self._session.logger.log("message", 0, conv["data"], 
                                         conv["user"], conv["dest"], conv["time"])


        def __user_to_account(self,user):

            for account in self._session.contacts.contacts.keys():
                if(account.lower() == user.lower()):
                    user = account

            founded_account = self._session.contacts.get(user)

            if(founded_account != None):
                return e3.Logger.Account.from_contact( founded_account )
            else:
                return e3.Logger.Account.from_contact( e3.base.Contact(user) )


        def __dest_user(self,conv_id):

             users = []

             users_dest = self.__conn_src.cursor()
             users_dest.execute(EM1_SELECT_DEST_USER % (conv_id,self.__myuser))

             for user_found in users_dest:
                 users.append(self.__user_to_account(user_found[0]))

             return users


        def __time_conversion(self,time):
            return date.fromtimestamp(time)


        def __data_conversion(self,data):
            d=data.partition("UTF-8\r\n")
            end=d[2].encode('UTF-8')
            return end



