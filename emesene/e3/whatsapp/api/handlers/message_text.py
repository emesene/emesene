from base import BaseHandler

class MessageText(BaseHandler):
    TAG = "message"
    SUBTAG = "body"

    EVENTS = ['message_received', 'server_notice_received',
            'group_message_received']

    def handle(self, xml):
        messagetype = xml.get("type")
        if messagetype != "chat":
            # Only handle chat messages, not subjects.
            return

        sender = xml.get("from")
        mid = xml.get("id")
        text = xml.find("body").text

        if sender == "Server@s.whatsapp.net":
            # Server notice
            self.waclient.trigger_event('server_notice_received', mid,
                    text)
        else:
            realname = xml.find("{urn:xmpp:whatsapp}notify").get("name")
            offline_stamp = None

            if xml.find("{urn:xmpp:delay}delay") is not None:
                raw_stamp = xml.find("{urn:xmpp:delay}delay").get("stamp")
                offline_stamp = self.waclient.parse_xmpp_time(raw_stamp)

            if sender.endswith("@g.us"):
                # Group message
                author = xml.get("author")
                self.waclient.trigger_event('group_message_received', mid,
                        sender, author, text, realname, offline_stamp)
            else:
                # Normal text message
                self.waclient.trigger_event('message_received', mid, sender,
                        text, realname, offline_stamp)
