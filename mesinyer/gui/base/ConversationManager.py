import e3
import MarkupParser

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
            self.session.signals.conv_message.subscribe(
                self._on_message)
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
            self.session.signals.contact_attr_changed.subscribe(
                self._on_contact_attr_changed)

    def add_new_conversation(self, session, cid, members):
        """
        create and append a new conversation
        """
        raise NotImplementedError("This method is not implemented")

    def _on_message(self, cid, account, message, cedict=None):
        '''called when a message is received'''
        conversation = self.conversations.get(float(cid), None)

        if conversation is None:
            conversation = self.new_conversation(cid, [account])

        conversation.on_receive_message(message, account, cedict)

        if message.type != e3.Message.TYPE_TYPING:
            self.set_message_waiting(conversation, True)

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

    def _on_message_send_failed(self, cid, message):
        '''called when a message is received'''
        conversation = self.conversations.get(float(cid), None)

        if conversation is not None:
            error = conversation.formatter.format_error(
                'message couldn\'t be sent: ')
            conversation.output.append(error,self.session.config.b_allow_auto_scroll)
            conversation.output.append(
                self.format_from_message(message),self.session.config.b_allow_auto_scroll)
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

    def new_conversation(self, cid, members=None):
        '''create a new conversation widget and append it to the tabs,
        if the cid already exists or there is already a conversation with
        that member, return the existing conversation.
        this method returns a tuple containing a boolean and a conversation
        object. If the conversation already exists, return True on as first
        value'''
        cid = float(cid)
        if cid in self.conversations:
            return self.conversations[cid]
        elif members is not None:
            for (key, conversation) in self.conversations.iteritems():
                if conversation.members == members:
                    old_cid = conversation.cid

                    if old_cid in self.conversations:
                        del self.conversations[old_cid]

                    conversation.cid = cid
                    self.conversations[cid] = conversation
                    return conversation

        conversation = self.add_new_conversation(self.session, cid, members)
        self.conversations[cid] = conversation

        return conversation

    def _on_contact_attr_changed(self, account, change_type, old_value,
            do_notify=True):
        '''called when an attribute of a contact changes'''
        for conversation in self.conversations.values():
            if account in conversation.members:
                conversation.update_data()

    def on_conversation_close(self, conversation):
        """
        called when the user wants to close a conversation widget
        """
        self.close(conversation)

        if len(self.conversations) == 0:
            self.on_last_close()

    def close(self, conversation):
        '''close a conversation'''
        self.session.close_conversation(conversation.cid)
        self.remove_conversation(conversation)
        del self.conversations[conversation.cid]
        conversation.on_close()

    def close_all(self):
        '''close and finish all conversations'''
        conversations = self.conversations.values()
        for conversation in conversations:
            self.close(conversation)

