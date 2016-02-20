from base import BaseHandler

class MessageChatstate(BaseHandler):
    TAG = "message"
    SUBNS = "http://jabber.org/protocol/chatstates"

    EVENTS = ['chatstate_changed']

    def handle(self, xml):
        sender = xml.get("from")
        state = xml[0].tag.split('}', 1)[1]

        self.waclient.trigger_event('chatstate_changed', sender, state)
