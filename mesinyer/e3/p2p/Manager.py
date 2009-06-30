import Queue
import threading

import protocol.Action

from debugger import dbg

class Manager(threading.Thread):
    '''P2P manager, a single thread for everything'''

    (ACTION_REGISTER, ACTION_UNREGISTER, ACTION_INPUT, ACTION_QUIT) = range(4)

    def __init__(self, input, output, mail):
        threading.Thread.__init__(self)

        self.mail = mail

        self.switchboard = SwitchboardTransport(self)

        self.input = input
        self.output = output

    def output_action(self, id_, *args):
        self.output.put(protocol.Action(id_, *args))

    def run(self):
        while True:
            try:
                if self.process(self.input.get(True)) == True:
                    return
            except Queue.Empty:
                pass

    def process(self, data):
        action, args = data
        
        if action == Manager.ACTION_REGISTER:
            self.switchboard.register(*args)

        elif action == Manager.ACTION_UNREGISTER:
            self.switchboard.unregister(*args)

        elif action == Manager.ACTION_INPUT:
            self.receive(self.switchboard.parse(*args))

        elif action == Manager.ACTION_QUIT:
            return True

    def receive(self, payload):
        # tlp.receive?
        dbg("p2p manager receive payload size " + len(payload), 'p2p', 3)


class SwitchboardTransport(object):
    '''Implementation of switchboard-specific methods'''

    def __init__(self, parent):
        self.manager = parent
        self.mail = self.manager.mail  # read as "self mail"
        self.cids = {}

    def register(self, mail, cid):
        self.cids.setdefault(mail, [])
        if cid not in self.cids:
            self.cids.append(cid)

    def unregister(self, mail, cid):
        if cid in self.cids.get(mail):
            self.cids.remove(cid)

        if self.cids.get(mail) == []:
            del self.cids[mail]

    def request(self, mail):
        '''Returns a valid cid'''
        if self.cids.get(mail, []):
            return self.cids[mail][0]
        else:
            cid = time.time()
            self.manager.output_action(Action.ACTION_NEW_CONVERSATION, (mail, cid))
            return cid

    def parse(self, mail, message):
        '''Returns the payload of a MsnMessage
        This would be implemented differently in another connection'''
        return message.body

    def send(self, mail, body):
        '''Builds a P2P Message and sends Worker a ACTION_SEND_MESSAGE
        with cid returned by self.request.'''
        message = e3.Message(e3.Message.TYPE_P2P, body, self.mail,
            dest=mail)
        self.manager.output_action(protocol.Action.ACTION_SEND_MESSAGE,
            (self.request(mail), message))
