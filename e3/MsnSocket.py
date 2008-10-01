'''defines an object that handles msn commands received from a socket'''

import common
import Socket
import Command


class MsnSocket(Socket.Socket):
    '''a socket object specialized to be used to connecto with the msn network
    '''

    def __init__(self, host='messenger.hotmail.com', port=1863, *args, **kwds):
        '''class constructor, args is there to be compatible with 
        MsnHttpSocket constructor'''
        Socket.Socket.__init__(self, host, port)
        self.tid = 1

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
    
    def _receive(self):
        '''receive data from the socket'''
        data = self._readline()
        # if we got something add it to the output queue
        if data:
            command = Command.Command.parse(data)

            if command.command in common.PAYLOAD_CMDS:
                position = common.PAYLOAD_POSITION[command.command]

                if position == -1:
                    size = int(command.tid)
                else:
                    size = int(command.params[position])

                command.payload = self.receive_fixed_size(size)

            self.output.put(command)

