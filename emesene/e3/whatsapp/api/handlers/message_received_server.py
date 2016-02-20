from base import BaseHandler

class MessageReceivedServer(BaseHandler):
    TAG = "message"
    SUBTAG = "x"
    SUBNS = "jabber:x:event"

    EVENTS = ['message_received_at_server']

    def handle(self, xml):
        sender = xml.get("from")
        mid = xml.get("id")

        self.waclient.trigger_event('message_received_at_server', sender, mid)
