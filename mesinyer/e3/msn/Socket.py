'''defines a class that handles the send and receive operations of a socket
in a thread'''

import Queue
import socket
import select
import StringIO
import threading

from debugger import dbg

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

    def quit(self):
        '''close the thread'''
        self.send('quit')

    def run(self):
        '''the main method of the socket, wait until there is something to 
        send or there is something to read, if there is something to send, get 
        it from the input Queue, wait until we can send it and send it, if 
        there is something to read, read it and put it on the output queue'''
        self.socket.connect((self.host, self.port))
        input_ = None

        while True:
            # see if we can send or read something
            (iwtd, owtd) = select.select([self], [self], [])[:2]

            # if we can read, we try to read
            if iwtd:
                if not self._receive():
                    # nothing received, socket closed
                    break
                # do not write until everything is read
                continue

            try:
                input_ = self.input.get(True, 0.3)

                if input_ == 'quit':
                    break
            except Queue.Empty:
                # nothing to send
                continue

            if owtd and input_:
                # try to get something to send, wait 0.3 seconds
                try:
                    self.socket.send(input_)
                    dbg('>>> ' + str(input_), 'sock', 2)
                except socket.error:
                    self._on_socket_error()
                    break

        dbg('closing socket thread', 'sock', 1)
        self.socket.close()

    def fileno(self):
        '''method that is used by select'''
        return self.socket.fileno()

    def _receive(self):
        '''receive data from the socket'''
        data = self._readline()
        # if we got something add it to the output queue
        if data:
            dbg('<<< ' + data, 'sock', 3)
            self.output.put(data)
            return True
        return False

    def _readline(self):
        '''read until new line'''
        output = StringIO.StringIO()

        try:
            chunk = self.socket.recv(1)
        except socket.error:
            self._on_socket_error()
            return None

        while chunk != '\n' and chunk != '':
            output.write(chunk)
            try:
                chunk = self.socket.recv(1)
            except socket.error:
                self._on_socket_error()

        if chunk == '\n':
            output.write(chunk)

        output.seek(0)
        return output.read()

    def receive_fixed_size(self, size):
        '''receive a fixed size of bytes, return it as string'''
        output = StringIO.StringIO()

        while output.len < size:
            try:
                output.write(self.socket.recv(size - output.len))
            except socket.error:
                self._on_socket_error()

        output.seek(0)

        return output.read()

    def _on_socket_error(self):
        '''send a message that the socket was closed'''
        self.output.put(0)
