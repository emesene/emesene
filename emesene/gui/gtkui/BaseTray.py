'''base class for tray icon like implementations'''

class BaseTray(object):
    '''
    a base tray icon class to reuse code
    '''

    def __init__(self):
        self.conversations = None

    def set_conversations(self, convs):
        """
        Sets the conversations manager
        """
        self.conversations = convs

    def set_contacts(self, contacts):
        """
        sets the contacts
        """
        pass

    def set_login(self):
        """
        dummy,messaging menu doesn't have a login state
        """
        pass


    def _get_conversation_manager(self, cid, account=None):
        '''
        return a conversation manager that matches cid and/or members
        '''
        if not self.conversations:
            return None

        for convman in self.conversations:
            if account:
                if convman.has_similar_conversation(cid, [account]):
                    return convman
            elif cid in convman.conversations:
                return convman

        return None

    def _get_conversation(self, cid, account=None):
        '''
        return a conversation that matches cid and/or members
        '''
        if not self.conversations:
            return None

        for convman in self.conversations:
            if account:
                conversation = convman.has_similar_conversation(cid, [account])
            else:
                conversation = convman.conversations.get(cid, None)

            if conversation:
                return conversation

        return None

