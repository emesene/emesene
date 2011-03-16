from synch import synch
import sqlite3.dbapi2 as sqlite
from datetime import date

class emesenesynch(synch):

        def __init__(self):
                synch.__init__(self)

        def start_synch(self, session, synch_function=None):

            synch.start_synch(self, session, synch_function)
		
            self.__conn_src = sqlite.connect(self.src_path)

            #get new users

            users = self.__conn_src.cursor()

            users.execute("select * from user")

            self.__conn_dest = sqlite.connect(self.dest_path)

            dest_users = self.__conn_dest.cursor()

            dest_users.execute("select * from d_account")

            user_names=[]

            for dest_user in dest_users:
                user_names.append(dest_user[1])

            for user in users:

                found=0

                for dest_user in user_names:
                    if(user[1]==dest_user):
                        found=1
                if found == 0:
                    print user[1]#insert the new user: insert into d_account (account,enabled) values ('blabla', 1)

            #EVENT message 0 TEXT OF MESSAGE <account 'mail1'> <account 'mail2'>


            #get new conversations		

            conversations = self.__conn_src.cursor()

            conversations.execute("select account,started,data from user inner join conversation_event on ( user.id=conversation_event.id_user ) inner join conversation on(conversation.id=conversation_event.id_conversation)")

            conversations_attr=[]

            for conv in conversations:
                conversations_attr.append({"user":self.__user_to_id(conv[0]),"time":conv[1],"data":self.__data_conversion(conv[2])})

                """for conv in conversations_attr:
                        print conv["user"]
                        print conv["data"]
                        print conv["time"]"""

        def __user_to_id(self,user):
            dest_users_id = self.__conn_dest.cursor()
            dest_users_id.execute("select id_account from d_account where account='%s'" % (user))
            for id_found in dest_users_id:
                return id_found[0]

	def __time_conversion(self,time):
            return date.fromtimestamp(time)

	def __data_conversion(self,data):
            d=data.partition("UTF-8\r\n")
            end=d[2].encode('UTF-8')
            return end



