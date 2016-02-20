from base import BaseHandler

class MessageReceivedClient(BaseHandler):
    TAG = "message"
    SUBTAG = "received"
    SUBNS = "urn:xmpp:receipts"

    EVENTS = ['message_received_at_client']

    def handle(self, xml):
        sender = xml.get("from")
        mid = xml.get("id")

        self.waclient.trigger_event('message_received_at_client', sender, mid)
