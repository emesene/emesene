import sys
import time
import Queue
import random

import protocol.Worker
import protocol.Message
import protocol.Contact
import protocol.Group
from  protocol.Event import Event
from  protocol.Action import Action
from protocol import status

import protocol.Logger as Logger
from debugger import dbg

class Worker(protocol.Worker):
    '''dummy Worker implementation to make it easy to test emesene'''

    def __init__(self, app_name, session, proxy, use_http=False):
        '''class constructor'''
        protocol.Worker.__init__(self, app_name, session)
        self.session = session

    def run(self):
        '''main method, block waiting for data, process it, and send data back
        '''
        data = None

        while True:
            try:
                action = self.session.actions.get(True, 0.1)

                if action.id_ == Action.ACTION_QUIT:
                    dbg('closing thread', 'dworker', 1)
                    self.session.logger.quit()
                    break

                self._process_action(action)
            except Queue.Empty:
                pass

    def _fill_contact_list(self):
        """
        method to fill the contact list with something
        """
        self._add_contact('dx@emesene.org', 'XD', status.ONLINE, '', False)
        self._add_contact('roger@emesene.org', 'r0x0r', status.ONLINE,
                '', False)
        self._add_contact('boyska@emesene.org', 'boyska', status.ONLINE,
                '', True)
        self._add_contact('pochu@emesene.org', '<3 debian', status.BUSY,
                '', False)
        self._add_contact('cloud@emesene.org', 'nube', status.BUSY,
                '', False)
        self._add_contact('otacon@emesene.org', 'Otacon', status.BUSY,
                '', True)
        self._add_contact('federico@emesene.org', 'federico..', status.AWAY,
                'he loves guiness', False)
        self._add_contact('respawner@emesene.org', 'Respawner', status.AWAY,
                '', False)
        self._add_contact('mohrtutchy@emesene.org', 'moh..', status.AWAY,
                'one love', True)
        self._add_contact('nassty@emesene.org', 'nassto', status.IDLE,
                '', False)
        self._add_contact('j0hn@emesene.org', 'juan', status.IDLE, '', False)
        self._add_contact('c0n0@emesene.org', 'conoconocono', status.IDLE,
                '', True)
        self._add_contact('warlo@emesene.org', 'warlo', status.OFFLINE,
                '', False)
        self._add_contact('wariano@emesene.org', 'wariano', status.OFFLINE,
                '', False)
        self._add_contact('Faith_Nahn@emesene.org', 'Gtk styler', status.BUSY,
                '', False)
        self._add_contact('you@emesene.org', 'I\'m on emesene code!',
                status.OFFLINE, '', True)

        self._add_group('ninjas')
        self._add_group('pirates')
        self._add_group('lulz')
        self._add_group('code quiz ninjas')
        self._add_group('empty')

        self._add_contact_to_group('you@emesene.org', 'pirates')
        self._add_contact_to_group('boyska@emesene.org', 'pirates')
        self._add_contact_to_group('j0hn@emesene.org', 'pirates')
        self._add_contact_to_group('c0n0@emesene.org', 'pirates')
        self._add_contact_to_group('nassty@emesene.org', 'lulz')
        self._add_contact_to_group('warlo@emesene.org', 'lulz')
        self._add_contact_to_group('you@emesene.org', 'lulz')
        self._add_contact_to_group('cloud@emesene.org', 'lulz')
        self._add_contact_to_group('dx@emesene.org', 'ninjas')
        self._add_contact_to_group('roger@emesene.org', 'ninjas')
        self._add_contact_to_group('c0n0@emesene.org', 'ninjas')
        self._add_contact_to_group('boyska@emesene.org', 'ninjas')
        self._add_contact_to_group('Faith_Nahn@emesene.org', 'code quiz ninjas')

    def _add_contact(self, mail, nick, status_, alias, blocked):
        """
        method to add a contact to the contact list
        """
        self.session.contacts.contacts[mail] = protocol.Contact(mail, mail,
            nick, '...', status_, alias, blocked)

    def _add_group(self, name):
        """
        method to add a group to the contact list
        """
        self.session.groups[name] = protocol.Group(name, name)

    def _add_contact_to_group(self, account, group):
        """
        method to add a contact to a group
        """
        self.session.groups[group].contacts.append(account)
        self.session.contacts.contacts[account].groups.append(group)

    # action handlers
    def _handle_action_add_contact(self, account):
        '''handle Action.ACTION_ADD_CONTACT
        '''
        self.session.add_event(Event.EVENT_CONTACT_ADD_SUCCEED,
            account)

    def _handle_action_add_group(self, name):
        '''handle Action.ACTION_ADD_GROUP
        '''
        self.session.add_event(Event.EVENT_GROUP_ADD_SUCCEED,
            name)

    def _handle_action_add_to_group(self, account, gid):
        '''handle Action.ACTION_ADD_TO_GROUP
        '''
        self.session.add_event(Event.EVENT_GROUP_ADD_CONTACT_SUCCEED,
            gid, account)

    def _handle_action_block_contact(self, account):
        '''handle Action.ACTION_BLOCK_CONTACT
        '''
        self.session.add_event(Event.EVENT_CONTACT_BLOCK_SUCCEED, account)

    def _handle_action_unblock_contact(self, account):
        '''handle Action.ACTION_UNBLOCK_CONTACT
        '''
        self.session.add_event(Event.EVENT_CONTACT_UNBLOCK_SUCCEED,
            account)

    def _handle_action_change_status(self, status_):
        '''handle Action.ACTION_CHANGE_STATUS
        '''
        self.session.add_event(Event.EVENT_STATUS_CHANGE_SUCCEED, status_)

    def _handle_action_login(self, account, password, status_):
        '''handle Action.ACTION_LOGIN
        '''
        self.session.add_event(Event.EVENT_LOGIN_SUCCEED)
        self.session.add_event(Event.EVENT_NICK_CHANGE_SUCCEED,
                'dummy nick is dummy')
        self._fill_contact_list()
        self.session.add_event(Event.EVENT_CONTACT_LIST_READY)

    def _handle_action_logout(self):
        '''handle Action.ACTION_LOGOUT
        '''

    def _handle_action_move_to_group(self, account, src_gid, dest_gid):
        '''handle Action.ACTION_MOVE_TO_GROUP
        '''
        self.session.add_event(Event.EVENT_CONTACT_MOVE_SUCCEED,
            account, src_gid, dest_gid)

    def _handle_action_remove_contact(self, account):
        '''handle Action.ACTION_REMOVE_CONTACT
        '''
        self.session.add_event(Event.EVENT_CONTACT_REMOVE_SUCCEED, account)

    def _handle_action_reject_contact(self, account):
        '''handle Action.ACTION_REJECT_CONTACT
        '''
        self.session.add_event(Event.EVENT_CONTACT_REJECT_SUCCEED, account)

    def _handle_action_remove_from_group(self, account, gid):
        '''handle Action.ACTION_REMOVE_FROM_GROUP
        '''
        self.session.add_event(Event.EVENT_GROUP_REMOVE_CONTACT_SUCCEED,
            gid, account)

    def _handle_action_remove_group(self, gid):
        '''handle Action.ACTION_REMOVE_GROUP
        '''
        self.session.add_event(Event.EVENT_GROUP_REMOVE_SUCCEED, gid)

    def _handle_action_rename_group(self, gid, name):
        '''handle Action.ACTION_RENAME_GROUP
        '''
        self.session.add_event(Event.EVENT_GROUP_RENAME_SUCCEED,
            gid, name)

    def _handle_action_set_contact_alias(self, account, alias):
        '''handle Action.ACTION_SET_CONTACT_ALIAS
        '''
        self.session.add_event(Event.EVENT_CONTACT_ALIAS_SUCCEED, account)

    def _handle_action_set_message(self, message):
        '''handle Action.ACTION_SET_MESSAGE
        '''
        self.session.add_event(Event.EVENT_MESSAGE_CHANGE_SUCCEED, message)

    def _handle_action_set_nick(self, nick):
        '''handle Action.ACTION_SET_NICK
        '''
        self.session.add_event(Event.EVENT_NICK_CHANGE_SUCCEED, nick)

    def _handle_action_set_picture(self, picture_name):
        '''handle Action.ACTION_SET_PICTURE
        '''
        pass

    def _handle_action_set_preferences(self, preferences):
        '''handle Action.ACTION_SET_PREFERENCES
        '''
        pass

    def _handle_action_new_conversation(self, account, cid):
        '''handle Action.ACTION_NEW_CONVERSATION
        '''
        pass

    def _handle_action_close_conversation(self, cid):
        '''handle Action.ACTION_CLOSE_CONVERSATION
        '''
        pass

    def _handle_action_send_message(self, cid, message):
        '''handle Action.ACTION_SEND_MESSAGE
        cid is the conversation id, message is a Message object
        '''
        self.session.add_event(Event.EVENT_CONV_MESSAGE_SEND_SUCCEED,
            cid, message)
        account = random.choice(self.session.contacts.contacts.keys())
        self.session.add_event(Event.EVENT_CONV_MESSAGE,
            cid, account, message)

    # p2p handlers

    def _handle_action_p2p_invite(self, cid, pid, dest, type_, identifier):
        '''handle Action.ACTION_P2P_INVITE,
         cid is the conversation id
         pid is the p2p session id, both are numbers that identify the 
            conversation and the session respectively, time.time() is 
            recommended to be used.
         dest is the destination account
         type_ is one of the protocol.Transfer.TYPE_* constants
         identifier is the data that is needed to be sent for the invitation
        '''
        pass

    def _handle_action_p2p_accept(self, pid):
        '''handle Action.ACTION_P2P_ACCEPT'''
        pass

    def _handle_action_p2p_cancel(self, pid):
        '''handle Action.ACTION_P2P_CANCEL'''
        pass
