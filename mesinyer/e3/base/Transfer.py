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
        self.fraction = 0

    def __str__(self):
        '''return a string representation of a file transfer'''
        return '<e3.base.filetransfer filename="%s" len="%i">' % (self.filename,
            len(self.data))

