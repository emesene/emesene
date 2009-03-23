
class Proxy(object):
    """
    This class represents the information of a proxy
    """

    def __init__(self, use_proxy=False, host='', port='', use_auth=False, 
        user='', passwd=''):
        """
        Constructor.
        use_proxy -- boolean that indicates if the proxy should be used
        host -- the host url
        port -- the port number
        use_auth -- a boolean that indicates if authentication should be used
        user -- the user of the proxy
        passwd -- the password of the user
        """
        self.use_proxy = use_proxy
        self.host = host
        self.port = port
        self.use_auth = use_auth
        self.user = user
        self.passwd = passwd
