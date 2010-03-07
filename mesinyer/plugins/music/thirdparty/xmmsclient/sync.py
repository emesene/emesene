
import xmmsapi

class XMMSSync:
    """
    A wrapper for the xmmsclient.XMMS class which simplifies synchronous
    communication with the XMMS2 daemon.

    Instances of this class may be used just like regular xmmsclient.XMMS
    objects, except that instead of returning an XMMSResult instance, the
    value associated with the result is returned.  If the XMMSResult
    indicates an error, an XMMSError is raised instead of returning the
    value.
    """
    def __init__(self, clientname=None, xmms=None):
        """
        This constructor takes two optional arguments. If xmms is omitted
        it will create a new underlying XMMS class otherwise it will use
        the one supplied. Clientname is the name of the client and will
        default to "Unnamed Python Client"
        """
        if xmms is None:
            self.__xmms = xmmsapi.XMMS(clientname)
        else:
            self.__xmms = xmms
            
    def __getattr__(self, name):
        attr = getattr(self.__xmms, name)
        if callable(attr):
            def _(*args, **kwargs):
                ret = attr(*args, **kwargs)
                if isinstance(ret, xmmsapi.XMMSResult):
                    ret.wait()
                    if ret.iserror():
                        raise XMMSError(ret.get_error())
                    return ret.value()
                return ret
            try:
                _.__doc__ = attr.__doc__
                _.func_name = '<sync version of %s>' % name
            except:
                pass
            return _
        else:
            return attr

class XMMSError(Exception):
    """
    Thrown when a synchronous method call on an XMMS client object fails.
    """
    pass
