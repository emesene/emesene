from base import BaseHandler

class GroupInfo(BaseHandler):
    TAG = "iq"
    SUBTAG = "group"

    EVENTS = ['group_info_received']

    def handle(self, xml):
        group = xml.find('group')

        groupid = group.get("id") + '@g.us'
        owner = group.get("owner")
        creation = group.get("creation")
        subject = group.get("subject")
        joindate = group.get("s_t")

        self.waclient.trigger_event('group_info_received', groupid, owner,
                creation, subject, joindate)
