import time
import Queue
import urllib2
import threading

import e3
import common
import Command

import logging
log = logging.getLogger('msn.MsnHttpSocket')

class MsnHttpSocket(threading.Thread):
    '''a socket that runs on a thread, it reads the data and put it on the
    output queue, the data to be sent is added to the input queue'''

    def __init__(self, dest_ip='messenger.hotmail.com', port_unused=1863,
        dest_type='SB', proxy=None):
        '''class contructor, port_unused is unused (duh!) but there for
        API compatibility with MsnSocket'''
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.tid = 1

        if proxy is None:
            self.proxy = e3.Proxy()
        else:
            self.proxy = proxy

        self.host = 'http://gateway.messenger.hotmail.com'
        self.dest_type = dest_type
        self.dest_ip = dest_ip
        self.path = '/gateway/gateway.dll?Action=open&Server=' + \
                    self.dest_type + '&IP=' + self.dest_ip
        self.session_id = None
        self.timestamp = time.time()

        if self.proxy.use_proxy:
            proxy_info = {'host': self.proxy.host, 'port' : self.proxy.port}

            if self.proxy.use_auth:
                proxy_info['user'] = self.proxy.user
                proxy_info['pass'] = self.proxy.passwd

                proxy_support = urllib2.ProxyHandler({"http" : \
                "http://%(user)s:%(pass)s@%(host)s:%(port)s" % proxy_info})
            else:
                proxy_support = urllib2.ProxyHandler({"http" : \
                "http://%(host)s:%(port)s" % proxy_info})

            opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)

            # install it
            urllib2.install_opener(opener)
        
        self.input = Queue.Queue()
        self.output = Queue.Queue()
        self.setDaemon(True)

    def send(self, data):
        '''add data to the input queue'''
        self.input.put(data)

    def send_command(self, command, params=None, payload=None):
        '''send command to the socket appending the tid and incrementing it, 
        append the parameters if not None'''

        if params:
            if payload:
                self.send('%s %d %s %d\r\n%s' % \
                  (command, self.tid, ' '.join(params), len(payload), payload))
            else:
                self.send('%s %d %s\r\n' % \
                  (command, self.tid, ' '.join(params)))
        else:
            if payload:
                self.send('%s %d %d\r\n%s' % \
                    (command, self.tid, len(payload), payload))
            else:
                self.send('%s %d\r\n' % (command, self.tid))

        self.tid += 1

    def run(self):
        '''the main method of the socket, wait until there is something to 
        send or there is something to read, if there is something to send, get 
        it from the input Queue, wait until we can send it and send it, if 
        there is something to read, read it and put it on the output queue'''
        input_ = None

        while True:
            # if we couldn't send the data the last loop we dont try to get 
            # another one
            if not input_:
                # try to get something to send, wait 1 second
                try:
                    input_ = []

                    while True:
                        command = self.input.get(True, 1.0)

                        if command == 'quit':
                            log.debug('closing socket thread')
                            break
                        else:
                            input_.append(command)
                except Queue.Empty:
                    # nothing to send
                    pass

            if input_:
                log.debug('>>> ' + '\n'.join(input_))
                self.send_req(''.join(input_))
                input_ = None
                self.timestamp = time.time()

            now = time.time()
            if (now - self.timestamp) > 4.0:
                self.timestamp = now
                self.poll()

    def poll(self):
        '''send a poll to the server and expect the response'''
        self.send_req('', '/gateway/gateway.dll?Action=poll&SessionID=' + \
            str(self.session_id))

    def send_req(self, data, path=None, is_retry=False):
        '''send a request to the server and expect the response'''

        if path is None:
            path = self.path
        
        url = self.host + path 

        request = urllib2.Request(url)
        request.add_header("Accept", "*/*")
        request.add_header("Accept-Language", "en-us")
        request.add_header("User-Agent", "MSMSGS")
        request.add_header("Proxy-Connection", "Keep-Alive")
        request.add_header("Connection", "Keep-Alive")
        request.add_header("Pragma", "no-cache")
        request.add_header("Content-Type", "application/x-msn-messenger")
        request.add_data(data)

        try:
            response = urllib2.urlopen(request)
            self.parse_response_header(response.info())
            self.parse_response_body(response.read())
        except Exception, ex:
            log.exception('exception on http request')
            # retry once
            if not is_retry:
                log.debug('retrying http request')
                self.send_req(data, path, True)


    def parse_response_header(self, info):
        '''parse the response header and do the changes on the variables'''
        if 'X-MSN-Messenger' in info:
            data = info['X-MSN-Messenger']
            self.session_id = data.split('; GW-IP=')[0].replace('SessionID=', 
                '')
            self.dest_ip = data.split('; ')[1].replace('GW-IP=', '')
            self.host = 'http://' + self.dest_ip
            self.path = '/gateway/gateway.dll?SessionID=' + self.session_id

    def parse_response_body(self, data):
        '''parse the response body'''
        if data:
            tail = data
            # to limit the number of loops if the data we receive is corrupted
            limit = 0

            while tail != '' and limit < 20:
                limit += 1
                head, tail = tail.split('\r\n', 1)

                command = Command.Command.parse(head + '\r\n')

                if command.command in common.PAYLOAD_CMDS:
                    position = common.PAYLOAD_POSITION[command.command]

                    if position == -1:
                        size = int(command.tid)
                    else:
                        size = int(command.params[position])

                    command.payload, tail = tail[:size], tail[size:]

                self.output.put(command)
