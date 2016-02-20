from base import BaseHandler

class GroupSubject(BaseHandler):
    TAG = "message"
    SUBTAG = "body"

    EVENTS = ['group_subject_changed']

    def handle(self, xml):
        messagetype = xml.get("type")
        if messagetype != "subject":
            # Only handle groupchat subject
            return

        groupid = xml.get("from")
        author = xml.get("author")
        subject = xml.find("body").text
        new = "event" in xml.attrib and xml.get("event") == "add"

        authorname = xml.find("{urn:xmpp:whatsapp}notify").get("name")
        offline_stamp = None

        if xml.find("{urn:xmpp:delay}delay") is not None:
            raw_stamp = xml.find("{urn:xmpp:delay}delay").get("stamp")
            offline_stamp = self.waclient.parse_xmpp_time(raw_stamp)

        self.waclient.trigger_event('group_subject_changed', groupid,
                subject, author, authorname, offline_stamp, new)
