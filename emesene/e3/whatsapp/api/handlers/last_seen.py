from base import BaseHandler

class LastSeen(BaseHandler):
    TAG = "iq"
    SUBTAG = "query"
    SUBNS = "jabber:iq:last"

    EVENTS = ['last_seen_received']

    def handle(self, xml):
        sender = xml.get("from")
        seconds = int(xml.find("{jabber:iq:last}query").get("seconds"))

        self.waclient.trigger_event('last_seen_received', sender, seconds)
