import e3
import e3.Worker as Worker
import e3.MsnSocket as MsnSocket
#import e3.MsnHttpSocket as MsnSocket
import protocol.Action as Action
from e3.Account import Account
from protocol.ContactManager import ContactManager

#from naf.nweb import Server
#from naf.nweb import validate
#from naf.nlocal import Server
#from naf.nlocal import validate
from naf.ngobject import Server;Server.set_events(e3.EVENTS)
from naf.ngobject import validate

class Core(Server):
    '''the class that builds a server that exposes the e3 library with a web
    API'''

    def __init__(self):
        '''class constructor'''
        Server.__init__(self)
        self.event_names = e3.EVENTS

        self.build()

    @validate(str)
    def get_contact_info(self, session, account="self"):
        '''return the information of a contact'''
        pass

    @validate(str)
    def get_contact_picture(self, session, account):
        '''return the picture associated with the account'''
        pass

    @validate()
    def get_pending_contacts(self, session):
        '''return the users that added us and are pending to be accepted'''
        pass

    @validate(str)
    def get_group_info(self, session, gid):
        '''return the information of a contact identified by gid'''
        pass

    @validate()
    def get_groups(self, session):
        '''return all the groups'''
        pass
    
    @validate()
    def get_contacts(self, session):
        '''return all the contacts'''
        pass
    
    @validate(str)
    def get_contacts_from_group(self, session, gid):
        '''return all the contacts of a group identified by gid'''
        pass

    @validate(str, str, int)
    def do_login(self, session, account, password, status):
        '''start the login process'''
        socket = MsnSocket('messenger.hotmail.com', 1863, dest_type='NS')
        worker = Worker('emesene2', socket, session, MsnSocket)
        socket.start()
        worker.start()

        session.account = Account(account, password, status, session.actions)
        session.protocol = self

        self.add_action(session, Action.ACTION_LOGIN, 
            (account, password, status))
        
    @validate()
    def do_logout(self, session):
        '''close the session'''
        self.add_action(session, Action.ACTION_LOGOUT, ())
        
    @validate(int)
    def do_change_status(self, session, status):
        '''change the status of the session'''
        self.add_action(session, Action.ACTION_CHANGE_STATUS, (status,))
        
    @validate(str)
    def do_add_contact(self, session, account):
        '''add the contact to our contact list'''
        self.add_action(session, Action.ACTION_ADD_CONTACT, (account,))
        
    @validate(str)
    def do_remove_contact(self, session, account):
        '''remove the contact from our contact list'''
        self.add_action(session, Action.ACTION_REMOVE_CONTACT, (account,))
        
    @validate(str)
    def do_block_contact(self, session, account):
        '''block the contact'''
        self.add_action(session, Action.ACTION_BLOCK_CONTACT, (account,))
        
    @validate(str)
    def do_unblock_contact(self, session, account):
        '''block the contact'''
        self.add_action(session, Action.ACTION_UNBLOCK_CONTACT, (account,))
        
    @validate(str, str)
    def do_set_contact_alias(self, session, account, alias):
        '''set the alias of a contact'''
        self.add_action(session, Action.ACTION_SET_CONTACT_ALIAS, 
            (account, alias))
        
    @validate(str, str)
    def do_add_to_group(self, session, account, gid):
        '''add a contact to a group'''
        self.add_action(session, Action.ACTION_ADD_TO_GROUP, (account, gid))
        
    @validate(str, str)
    def do_remove_from_group(self, session, account, gid):
        '''remove a contact from a group'''
        self.add_action(session, Action.ACTION_REMOVE_FROM_GROUP, 
            (account, gid))
        
    @validate(str, str, str)
    def do_move_to_group(self, session, account, src_gid, dest_gid):
        '''remove a contact from the group identified by src_gid and add it
        to dest_gid'''
        self.add_action(session, Action.ACTION_MOVE_TO_GROUP, (account, 
        src_gid, dest_gid))
        
    @validate(str)
    def do_add_group(self, session, name):
        '''add a group '''
        self.add_action(session, Action.ACTION_ADD_GROUP, (name,))
        
    @validate(str)
    def do_remove_group(self, session, gid):
        '''remove the group identified by gid'''
        self.add_action(session, Action.ACTION_REMOVE_GROUP, (gid,))
        
    @validate(str, str)
    def do_rename_group(self, session, gid, name):
        '''rename the group identified by gid with the new name'''
        self.add_action(session, Action.ACTION_RENAME_GROUP, (gid, name))
        
    @validate(str)
    def do_set_nick(self, session, nick):
        '''set the nick of the session'''
        self.add_action(session, Action.ACTION_SET_NICK, (nick,))

    @validate(str)
    def do_set_message(self, session, message):
        '''set the message of the session'''
        self.add_action(session, Action.ACTION_SET_MESSAGE, (message,))

    @validate(str)
    def do_set_picture(self, session, picture_name):
        '''set the picture of the session to the picture with picture_name as
        name'''
        self.add_action(session, Action.ACTION_SET_PICTURE, (picture_name,))
    
    @validate(dict)
    def do_set_preferences(self, session, preferences):
        '''set the preferences of the session to preferences, that is a 
        dict containing key:value pairs where the keys are the preference name
        and value is the new value of that preference'''
        self.add_action(session, Action.ACTION_SET_PREFERENCE, (preferences,))

    @validate(str, float)
    def do_new_conversation(self, session, account, cid):
        '''start a new conversation with account'''
        self.add_action(session, Action.ACTION_NEW_CONVERSATION, (account, cid))
    
    @validate()
    def do_quit(self, session):
        '''close the worker and socket threads'''
        self.add_action(session, Action.ACTION_QUIT, ())
    
    @validate(float, str)
    def do_send_message(self, session, cid, text):
        '''send a common message'''
        account = session.account.account
        message = e3.Message(e3.Message.TYPE_MESSAGE, text, account)
        self.add_action(session, Action.ACTION_SEND_MESSAGE, (cid, message))

