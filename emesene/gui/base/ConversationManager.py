# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
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

import e3

import logging
log = logging.getLogger('gui.base.ConversationManager')

class ConversationManager(object):
    '''the main conversation, it only contains other conversations'''

    def __init__(self, session, on_last_close):
        '''class constructor'''
        self.session = session
        self.on_last_close = on_last_close
        
        self.conversations = {}
        if self.session:
            self.subscribe_signals()

        conversation_tabs = self.session.config.get_or_set(
                'b_conversation_tabs', True)

        if self.session.conversations is None or conversation_tabs:
            self.session.conversations = {}

    def subscribe_signals(self):
        self.session.signals.conv_message.subscribe(
            self._on_message)
        self.session.signals.user_typing.subscribe(
            self._on_user_typing)
        self.session.signals.conv_contact_joined.subscribe(
            self._on_contact_joined)
        self.session.signals.conv_contact_left.subscribe(
            self._on_contact_left)
        self.session.signals.conv_group_started.subscribe(
            self._on_group_started)
        self.session.signals.conv_group_ended.subscribe(
            self._on_group_ended)
        self.session.signals.conv_message_send_failed.subscribe(
            self._on_message_send_failed)
        #self.session.signals.contact_attr_changed.subscribe(
        #    self._on_contact_attr_changed)
        self.session.signals.p2p_finished.subscribe(
            self._on_p2p_finished)

    def unsubscribe_signals(self):
        self.session.signals.conv_message.unsubscribe(
            self._on_message)
        self.session.signals.user_typing.unsubscribe(
            self._on_user_typing)
        self.session.signals.conv_contact_joined.unsubscribe(
            self._on_contact_joined)
        self.session.signals.conv_contact_left.unsubscribe(
            self._on_contact_left)
        self.session.signals.conv_group_started.unsubscribe(
            self._on_group_started)
        self.session.signals.conv_group_ended.unsubscribe(
            self._on_group_ended)
        self.session.signals.conv_message_send_failed.unsubscribe(
            self._on_message_send_failed)
        #self.session.signals.contact_attr_changed.unsubscribe(
        #    self._on_contact_attr_changed)
        self.session.signals.p2p_finished.unsubscribe(
            self._on_p2p_finished)

    def add_new_conversation(self, session, cid, members):
        """
        create and append a new conversation
        """
        raise NotImplementedError("This method is not implemented")

    def _on_message(self, cid, account, message, cedict=None):
        '''called when a message is received'''
        conversation = self.conversations.get(float(cid), None)
        conversation_tabs = self.session.config.get_or_set(
                'b_conversation_tabs', True)

        if conversation is None and conversation_tabs:
            conversation = self.new_conversation(cid, [account])

        if conversation is not None:
            conversation.on_receive_message(message, account, cedict)
            self.set_message_waiting(conversation, True)

    def _on_user_typing(self, cid, account, *args):
        """
        inform that the other user has started typing
        """
        conversation = self.conversations.get(float(cid), None)

        if conversation is None:
            return

        conversation.on_user_typing(account)

    def set_message_waiting(self, conversation, is_waiting):
        """
        inform the user that a message is waiting for the conversation
        """
        raise NotImplementedError("Method not implemented")

    def remove_conversation(self, conversation):
        """
        remove the conversation from the gui

        conversation -- the conversation instance
        """
        raise NotImplementedError("Method not implemented")

    def _on_message_send_failed(self, cid, error):
        '''called when a message failes to be sent'''
        conversation = self.conversations.get(float(cid), None)

        if conversation is not None:
            conversation.on_send_message_failed(error)
        else:
            log.debug('conversation %s not found' % cid)

    def _on_contact_joined(self, cid, account):
        '''called when a contact join the conversation'''
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_contact_joined(account)
        else:
            log.debug('on_contact_joined: conversation is None')

    def _on_contact_left(self, cid, account):
        '''called when a contact leaves the conversation'''
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_contact_left(account)
        else:
            log.debug('on_contact_left: conversation is None')

    def _on_group_started(self, cid):
        '''called when a group conversation starts'''
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_group_started()

    def _on_group_ended(self, cid):
        '''called when a group conversation ends'''
        conversation = self.conversations.get(float(cid), None)

        if conversation:
            conversation.on_group_ended()

    def format_from_message(self, message):
        '''return a markup text representing the format on the message'''
        return e3.common.add_style_to_message(message.body, message.style)

    def has_similar_conversation(self, cid, members=None):
        '''
        try to find a conversation with the given cid, if not search for a
        conversation with the same members and return it

        if not found return None
        '''
        cid = float(cid)

        if cid in self.conversations:
            return self.conversations[cid]

        elif members is not None:
            for conversation in self.conversations.itervalues():
                if conversation.members == members:
                    return conversation

        else:
            for conversation in self.conversations.itervalues():
                if conversation.icid == cid:
                    return conversation

    def reuse_conversation(self, cid, members):
        '''
        return an existing conversation if the cid is registered or there is
        a conversation with the same members

        *warning* this method updates the old conversation cid to the new
        if reused, don't use to check if the conversation is available

        otherwise return None
        '''
        conversation = self.has_similar_conversation(cid, members)

        if conversation:
            old_cid = conversation.cid

            if old_cid in self.conversations:
                del self.conversations[old_cid]
            if old_cid in self.session.conversations:
                del self.session.conversations[old_cid]

            conversation.cid = cid
            self.conversations[cid] = conversation
            self.session.conversations[cid] = conversation
            return conversation

        return None

    def new_conversation(self, cid, members=None):
        '''create a new conversation widget and append it to the tabs,
        if the cid already exists or there is already a conversation with
        that member, return the existing conversation.
        this method returns a tuple containing a boolean and a conversation
        object. If the conversation already exists, return True on as first
        value'''
        conversation = self.reuse_conversation(cid, members)

        if conversation is None:
            conversation = self.add_new_conversation(self.session, cid, members)
            self.conversations[cid] = conversation
            self.session.conversations[cid] = conversation

        self.after_new_conversation(conversation)
        return conversation

    def after_new_conversation(self, conversation):
        '''
         Override what to do after create a conversation
        '''
        pass

    def renew_session(self, session):
        '''reopen all conversations when the user reconnects'''
        self.session = session
        self.subscribe_signals()
        for cid, conversation in self.conversations.iteritems():
            conversation.session = session
            conversation.subscribe_signals()
            conversation.set_sensitive(True)
            account = conversation.members[0]
            self.new_conversation(cid, [account])
            self.session.new_conversation(account, cid)

    def close_session(self):
        '''unsubscribe all signals when the user gets disconnected
        and make the conversations insensitive'''
        for conversation in self.conversations.itervalues():
            conversation.unsubscribe_signals()
            conversation.set_sensitive(False)
        self.unsubscribe_signals() # but keep alive conversations

    def _on_contact_attr_changed(self, account, change_type, old_value,
            do_notify=True):
        '''called when an attribute of a contact changes'''
        for conversation in self.conversations.values():
            if account in conversation.members:
                conversation.update_data()

    def _on_p2p_finished(self, account, _type, *what):
        ''' called when a p2p is finished - currently custom emoticons only '''
        for conversation in self.conversations.values():
            if account in conversation.members:
                conversation.update_p2p(account, _type, *what)

    def on_conversation_close(self, conversation):
        """
        called when the user wants to close a conversation widget
        """
        # TODO: there is a strange case when changing the tabbed to no tabbed
        # config, for some reason that conversations don't seem to be removed
        self.close(conversation)

        if len(self.conversations) == 0:
            self.on_last_close()

    def close(self, conversation):
        '''close a conversation'''
        self.session.close_conversation(conversation.cid)
        self.remove_conversation(conversation)
        del self.conversations[conversation.cid]
        conversation.on_close()
        self.after_close()
        
    def after_close(self):
        '''
        Override what to do after close a conversation
        '''
        pass

    def close_all(self):
        '''close and finish all conversations'''
        self.unsubscribe_signals()
        for conversation in self.conversations.values():
            self.close(conversation)

    def present(self, conversation):
        '''
        present the given conversation
        '''
        raise NotImplementedError("not implemented")

    def get_dimensions(self):
        '''
        return dimensions of the conversation window, if more than one return
        the value of one of them
        '''
        raise NotImplementedError("not implemented")

    def hide_all(self):
        '''
        hide all conversations
        '''
        raise NotImplementedError("not implemented")

    def is_active(self):
        '''
        return True if the conversation manager is active
        '''
        raise NotImplementedError("not implemented")
