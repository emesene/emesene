
class Server(object):
    
    def __init__(self, host, port, name=""):
        self.host = host
        self.port = port
        self.name = name

    def to_dict(self):
        return {'host': self.host, 'port': self.port}

    def to_tuple(self):
        return (self.host, self.port)
