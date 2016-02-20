from base import BaseHandler

class GroupParticipants(BaseHandler):
    TAG = "iq"
    SUBTAG = "participant"

    EVENTS = ['group_participants_received']

    def handle(self, xml):
        groupid = xml.get('from')
        participants = []

        for participant in xml.findall('participant'):
            participants.append(participant.get('jid'))

        self.waclient.trigger_event('group_participants_received', groupid,
                participants)
