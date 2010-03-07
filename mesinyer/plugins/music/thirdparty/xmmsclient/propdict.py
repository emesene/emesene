class PropDict(dict):
    def __init__(self, srcs):
        dict.__init__(self)
        self._sources = srcs

    def set_source_preference(self, sources):
        """
        Change list of source preference
        This method has been deprecated and should no longer be used.
        """
        raise DeprecationWarning("This method has been deprecated and should no longer be used. Set the sources list using the 'sources' property.")
        self._set_sources(sources)

    def has_key(self, item):
        try:
            self.__getitem__(item)
            return True
        except KeyError:
            return False

    def __contains__(self, item):
        return self.has_key(item)

    def __getitem__(self, item):
        if isinstance(item, basestring):
            for src in self._sources:
                if src.endswith('*'):
                    for k,v in self.iteritems():
                        if k[0].startswith(src[:-1]) and k[1] == item:
                            return v
                try:
                    t = dict.__getitem__(self, (src, item))
                    return t
                except KeyError:
                    pass
            raise KeyError, item
        return dict.__getitem__(self, item)

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default
    
    def _get_sources(self):
        return self._sources
    def _set_sources(self, val):
        if isinstance(val, basestring):
            raise TypeError("Need a sequence of sources")
        for i in val:
            if not isinstance(i, basestring):
                raise TypeError("Sources need to be strings")
        self._sources = val
    sources = property(_get_sources, _set_sources)

