'''defines a class that handles the send and receive operations of a socket
in a thread'''

import Queue
import socket
import select
import StringIO
import threading

class Socket(threading.Thread):
    '''a socket that runs on a thread, it reads the data and put it on the 
    output queue, the data to be sent is added to the input queue'''

    def __init__(self, host, port):
        '''class constructor'''
        threading.Thread.__init__(self)

        self.host = host
        self.port = port

        self.input = Queue.Queue()
        self.output = Queue.Queue()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setDaemon(True)

    def send(self, data):
        '''add data to the input queue'''
        self.input.put(data)

    def run(self):
        '''the main method of the socket, wait until there is something to 
        send or there is something to read, if there is something to send, get 
        it from the input Queue, wait until we can send it and send it, if 
        there is something to read, read it and put it on the output queue'''
        self.socket.connect((self.host, self.port))
        input_ = None

        while True:
            # if we couldn't send the data the last loop we dont try to get 
            # another one
            if not input_:
                # try to get something to send, wait 0.3 seconds
                try:
                    input_ = self.input.get(True, 0.3)

                    if input_ == 'quit':
                        print 'closing socket thread'
                        break
                except Queue.Empty:
                    # nothing to send
                    pass

            # see if we can send or read something
            (iwtd, owtd) = select.select([self], [self], [self])[:2]

            # if we can write and there is something to write
            if owtd and input_:
                print '>>>', input_
                self.socket.send(input_)
                input_ = None

            # if we can read, we try to read
            if iwtd:
                self._receive()

    def fileno(self):
        '''method that is used by select'''
        return self.socket.fileno()

    def _receive(self):
        '''receive data from the socket'''
        data = self._readline()
        # if we got something add it to the output queue
        if data:
            print 'received', data
            self.output.put(data)

    def _readline(self):
        '''read until new line'''
        output = StringIO.StringIO()

        chunk = self.socket.recv(1)
        while chunk != '\n' and chunk != '':
            output.write(chunk) 
            chunk = self.socket.recv(1)
        
        if chunk == '\n':
            output.write(chunk)

        output.seek(0)
        return output.read()

    def receive_fixed_size(self, size):
        '''receive a fixed size of bytes, return it as string'''
        output = StringIO.StringIO()

        for byte_num in xrange(size):
            output.write(self.socket.recv(1))

        output.seek(0)

        return output.read()


    def reconnect(self, host, port):
        '''connect to a different host'''
        self.host = host
        self.port = port
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
