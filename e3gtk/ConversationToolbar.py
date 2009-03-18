import gtk

class ConversationToolbar(gtk.Toolbar):
    """
    A class that represents the toolbar on the conversation window
    """

    def __init__(self, handler):
        """
        constructor

        handler -- an instance of e3common.Handler.ConversationToolbarHandler
        """
        gtk.Toolbar.__init__(self)
        self.handler = handler
