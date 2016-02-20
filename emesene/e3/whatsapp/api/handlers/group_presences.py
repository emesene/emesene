from base import BaseHandler

class GroupPresences(BaseHandler):
    TAG = "presence"
    NS = "w"

    EVENTS = ['group_user_joined', 'group_user_removed']

    def handle(self, xml):
        groupid = xml.get("from")

        if "remove" in xml.attrib:
            user = xml.get("remove")
            author = xml.get("author")

            self.waclient.trigger_event('group_user_removed', groupid, user,
                    author)

        elif "add" in xml.attrib:
            user = xml.get("add")

            self.waclient.trigger_event('group_user_joined', groupid, user)
