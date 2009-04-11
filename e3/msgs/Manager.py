import time

import Queue
import threading

from e3 import Requester
from protocol import Action, Event

from Parser import MailDataParser
from debugger import dbg

class Manager(threading.Thread):
    '''Offline Messages Manager'''

    (ACTION_MSG_RECEIVED, ACTION_MAIL_DATA,
     ACTION_OIM_REQUEST, ACTION_OIM_SEND,
     ACTION_OIM_RECEIVED, ACTION_OIM_DELETE, ACTION_QUIT) = range(7)

    def __init__(self, session):
        '''Offline Messages Manager Constructor'''
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.input = Queue.Queue() #Input queue
        self.session = session

        self._set_handlers()

        self.waiting_requests = 0

        # requested oims
        self.requested = []

    def put(self, *data):
        '''Put an action in queue'''
        self.input.put(data)

    def quit(self):
        '''Quit thread'''
        self.put(Manager.ACTION_QUIT)

    def run(self):
        while True:
            try:
                if self.process(self.input.get(True)) == True:
                    return
            except Queue.Empty:
                pass

    def process(self, data):
        action, args = data[0], data[1:]
        
        if action == Manager.ACTION_OIM_DELETE:
            self._on_delete_oim(*args)

        elif action == Manager.ACTION_MAIL_DATA:
            self._on_oimdata_receive(*args)

        elif action == Manager.ACTION_OIM_REQUEST:
            self._on_oim_request(*args)
        
        elif action == Manager.ACTION_OIM_RECEIVED:
            self._on_oim_receive(*args)
       
        elif action == Manager.ACTION_OIM_SEND:
            self._on_oim_send(*args)

        elif action == Manager.ACTION_MSG_RECEIVED:
            self._on_msg_received(*args)

        elif action == Manager.ACTION_QUIT:
            return True

    def _set_handlers(self):
        '''Set handlers for msgs received from server'''
        srv_msg_handlers = {}

        srv_msg_handlers['initialmdatanotification'] = self._on_oimdata_receive
        srv_msg_handlers['oimnotification'] = self._on_oimdata_receive
        #srv_msg_handlers['initialemailnotification'] =  self._on_initial_mail
        #srv_msg_handlers['emailnotification'] = self._on_new_mail
        #srv_msg_handlers['activemailnotification'] =  self._on_move_mail
        #srv_msg_handlers['profile'] = self._on_msg_profile

        self._server_msg_handlers = srv_msg_handlers

    def _on_msg_received(self, message):
        '''Parse msg and call handler'''
        payload = {}
        for line in message.payload.split('\r\n'):
            if line:
                (key, value) = line.split(': ')
                if key == 'Content-Type':
                    value, charset = value.split('; ')
                    # removes text/x-msmsgs, it's allways the same
                    value = value.replace('text/x-msmsgs', '')
                    payload['charset'] = charset.split('=')[1]
                payload[key] = value

        handler = self._server_msg_handlers.get(payload['Content-Type'], None)

        if handler:
            handler(payload)
        else:
            self._on_unknown_msg(payload)
    
    def _on_oim_send(self, contact, message):
        '''Send an oim'''
        Requester.SendOIM(self.session, self.input, contact, message).start()
    
    def _on_delete_oim(self, oid):
        '''Delete an oim'''
        Requester.DeleteOIM(self.session, oid, self.input).start()

    # MSG handlers
    def _on_oimdata_receive(self, payload):
        '''parse Mail-Data and retrive oims'''

        if isinstance(payload, dict):
            payload = payload['Mail-Data']

        if payload != 'too-large':
            mail_data = MailDataParser(payload)
            oim_list = []
            for oim in mail_data.oims:
                self._on_oim_request(oim)
                oim_list.append(oim)
            for oim in oim_list:
                Requester.RetriveOIM(self.session, oim, self.input).start()
        else:
            dbg('[Too Large] retriving oims from a SOAP request', 'oim', 1)
            Requester.RetriveTooLarge(self.session, self.input).start()

    def _on_oim_request(self, oim):
        self.waiting_requests += 1

    def _on_oim_receive(self, oim):
        self.requested.append(oim)
        self.oims_notify()

    def _on_unknown_msg(self, payload):
        '''handle the unknown MSG'''
        dbg('unknown MSG: ' + str(payload['Content-Type']), 'oim', 1)

    def oims_notify(self):
        if self.waiting_requests == len(self.requested):
            self.requested.sort(key=lambda oim:oim.date)
            for oim in self.requested:
                dbg('[OIM] ' + oim.nick + ' ' + oim.mail + ' ' + str(oim.date) + \
                    ' ' + oim.message, 'oim', 1)
                #self.put(Manager.ACTION_OIM_DELETE, oim.id)
                self.session.add_event(Event.EVENT_OIM_RECEIVED, oim)
            self.waiting_requests = 0
            self.requested = []
