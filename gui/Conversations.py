import protocol.Object as Object

class Conversations(Object):
    '''this class contains one or more ConversationBase objects and allows
    different operations with them'''

    def __init__(self): 
        '''constructor'''
        Object.__init__(self)

        self.conversations = []
        self.current = None

        self.signal_add("conversation-added", 1)
        self.signal_add("conversation-removed", 1)

    def close_current(self):
        '''close the current conversation'''
        if self.current and self.current in self.conversations:
            old = self.current
            self.current.close()
            self.conversations.remove(self.current)
            self.update_current()
            self.signal_emit("conversation-removed", old)

    def update_current(self):
        '''update the self.current object to reflect the current selected
        conversation'''
        pass

    def add(self, conversation_base):
        '''add a ConversationBase object to conversations'''
        self.conversations.append(conversation_base)
        self.signal_emit("conversation-added", conversation_base)
