import e3
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
        session.login(self, account, password, status)
        
    @validate()
    def do_logout(self, session):
        '''close the session'''
        session.logout()
        
    @validate(int)
    def do_change_status(self, session, status):
        '''change the status of the session'''
        session.set_status(status)
        
    @validate(str)
    def do_add_contact(self, session, account):
        '''add the contact to our contact list'''
        session.add_contact(account)
        
    @validate(str)
    def do_remove_contact(self, session, account):
        '''remove the contact from our contact list'''
        session.remove_contact(account)
        
    @validate(str)
    def do_block_contact(self, session, account):
        '''block the contact'''
        session.block(account)
        
    @validate(str)
    def do_unblock_contact(self, session, account):
        '''block the contact'''
        session.unblock(account)
        
    @validate(str, str)
    def do_set_contact_alias(self, session, account, alias):
        '''set the alias of a contact'''
        session.set_alias(account)
        
    @validate(str, str)
    def do_add_to_group(self, session, account, gid):
        '''add a contact to a group'''
        session.add_to_group(account, gid)
        
    @validate(str, str)
    def do_remove_from_group(self, session, account, gid):
        '''remove a contact from a group'''
        session.remove_from_group(account, gid)
        
    @validate(str, str, str)
    def do_move_to_group(self, session, account, src_gid, dest_gid):
        '''remove a contact from the group identified by src_gid and add it
        to dest_gid'''
        session.move_to_group(account, src_gid, dest_gid)
        
    @validate(str)
    def do_add_group(self, session, name):
        '''add a group '''
        session.add_group(name)
        
    @validate(str)
    def do_remove_group(self, session, gid):
        '''remove the group identified by gid'''
        session.remove_group(gid)
        
    @validate(str, str)
    def do_rename_group(self, session, gid, name):
        '''rename the group identified by gid with the new name'''
        session.rename_group(gid, name)
        
    @validate(str)
    def do_set_nick(self, session, nick):
        '''set the nick of the session'''
        session.set_nick(nick)

    @validate(str)
    def do_set_message(self, session, message):
        '''set the message of the session'''
        session.set_message(message)

    @validate(str)
    def do_set_picture(self, session, picture_name):
        '''set the picture of the session to the picture with picture_name as
        name'''
        session.set_picture(picture_name)
    
    @validate(dict)
    def do_set_preferences(self, session, preferences):
        '''set the preferences of the session to preferences, that is a 
        dict containing key:value pairs where the keys are the preference name
        and value is the new value of that preference'''
        session.set_preferences(preferences)

    @validate(str, float)
    def do_new_conversation(self, session, account, cid):
        '''start a new conversation with account'''
        session.new_conversation(account, cid)
    
    @validate()
    def do_quit(self, session):
        '''close the worker and socket threads'''
        session.quit()
    
    @validate(float, str)
    def do_send_message(self, session, cid, text):
        '''send a common message'''
        session.send_message(cid, text)

