class ConversationBase(object):
    '''this class contains all the widgets and methods that are useful
    to build a conversation window but it doesnt arrange them in 
    any particular order, a subclass of it should define how the
    window should look like, in this way we can have more than
    one window look but having all the important stuff on one
    common place'''

    def __init__(self, conversation, contacts, groups, dialogs):
        '''class constructor'''
        self.conversation = conversation

        # you should set these to your implementation
        self.input = None
        self.output = None

        # an object that inheriths from gui.ContactList
        self.contacts = None

        self.image = None
        self.contact_image = None

    # override this methods to implement your toolkit
    def clear_input(self):
        '''clear the input text area'''
        pass

    def clear_output(self):
        '''clear the output text area'''
        pass

    def set_input_text(self, text):
        '''set the text on input, text is a base.Message object, returns 
        None if no message is available'''
        pass
    
    def set_output_text(self, text):
        '''set the text on output, text is a base.Message object, returns
        None if no message is available'''
        pass

    def append_input_text(self, text):
        '''append text to the input, text is a base.Message object'''
        pass

    def append_output_text(self, text):
        '''append text to the output, text is a base.Message object'''
        pass

    def get_input_message(self):
        '''return the content of input as a base.Message object'''
        pass

    def get_output_message(self):
        '''return the content of output as a base.Message object'''
        pass

    def set_image(self, path):
        '''set the image of self to the image located at path'''
        pass
    
    def set_contact_image(self, path):
        '''set the contact image to the image located at path'''
        pass

    # don't override this one if you don't want to add functionality
    def send_message(self):
        '''send the message on input'''
        message = self.get_input_message()

        if not message:
            return

        if self.conversation:
            self.conversation.signal_emit("message-sent", message)

        self.append_output_text(message)
        self.clear_input()

    def close(self):
        '''do all the operations to close the conversation'''
        if self.conversation:
            self.conversation.signal_emit("conversation-closing")
            self.conversation.signal_emit("conversation-closed")
