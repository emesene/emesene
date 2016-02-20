class BaseHandler:
    """Base handler class, each handler should inherit from this."""

    # Global tag to filter for
    TAG = ""
    # Global namespace to filter for
    NS = ""

    # Subtags to look for
    SUBTAG = ""
    # Samespace of subtag to look for.
    SUBNS = ""

    # All event this handler can trigger
    EVENTS = []

    def __init__(self, waclient):
        self.waclient = waclient

    def handle(xml):
        """This method will be called each time a message is received which
        matches the set options. The xml argument will contain the entire XML
        element including childeren.

        Override this method.

        Use self.waclient to access other parts of the api.
        Use self.waclient.trigger_event('event', arg1, ...) to trigger an event
        on the implementation side of the api."""

        pass
