class FileTransfer(object):
    '''a class that represent a file transfer'''
    (WAITING, TRANSFERING, RECEIVED, FAILED) = range(4)

    def __init__(self, obj, filename, size, preview, sender='Me'):
        self.filename = filename
        self.size = size
        self.preview = preview

        self.object = obj

        self.state = FileTransfer.WAITING
        self.sender = sender
        self.received_data = 0

        self.time_start = 0

    def __str__(self):
        '''return a string representation of a file transfer'''
        return '<e3.base.filetransfer filename="%s" len="%i">' % (self.filename,
            len(self.data))

    def get_progress(self):
        ''' returns the lenght of the received data '''
        return self.received_data

    def get_fraction(self):
        ''' received the percentage, which is < 0 and > 1 '''
        return (self.received_data / self.size)

    def get_eta(self):
        ''' returns the estimated time left to finish the transfer '''
        return ((self.size - self.received_data) / self.get_speed())
    
    def get_speed(self):
        ''' returns the average speed of the transfer '''
        return (self.received_data / self.get_time())

    def get_time(self):
        ''' returns the elapsed time since the start of the transfer '''
        return (time.time() - self.time_start)
