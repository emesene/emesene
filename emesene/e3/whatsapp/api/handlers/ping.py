from base import BaseHandler

class Ping(BaseHandler):
    TAG = "iq"
    SUBTAG = "ping"
    SUBNS = "urn:xmpp:ping"

    def handle(self, xml):
        ping_id = xml.get("id")
        self.waclient.send_pong(ping_id)
