from base import BaseHandler

class MessageAckRequest(BaseHandler):
    TAG = "message"
    SUBTAG = "request"
    SUBNS = "urn:xmpp:receipts"

    def handle(self, xml):
        sender = xml.get("from")
        mid = xml.get("id")

        self.waclient.send_message_ack(sender, mid)
