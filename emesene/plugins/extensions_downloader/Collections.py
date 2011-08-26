try:
	from urllib2 import urlopen
	from simplejson import loads
        import string

except ImportError, e:
	raise Exception('Required module missing: %s' % e.args[0])

API_GITHUB_FETCHBLOB = "http://github.com/api/v2/json/blob/all/emesene/%s/master"

class ExtensionDescriptor(object):

    def __init__(self):
        self.files = {}
        self.todownload = False

    def addFile(self, file_name, blob):
        self.files[file_name] = blob

class Collection(object):

    def __init__(self, theme):
        self.extensions_descs = {}
        self.theme = theme


    def plugin_name_from_file(self, file_name):
        pass


    def fetch(self):
        pass

class PluginsCollection(Collection):

    def plugin_name_from_file(self, file_name):
        ps = string.find(file_name, "/")

        if ps != -1:
            return file_name[:ps]
        else:
            return ps


    def fetch(self):

        response = urlopen(API_GITHUB_FETCHBLOB % self.theme)
        rq = response.read()
        j = loads(rq)
        type = "plugin"

        for k in j["blobs"]:

            plugin = self.plugin_name_from_file(k)

            if plugin == -1:
                continue

            try:
                extype = self.extensions_descs[type]
            except KeyError:
                extype = self.extensions_descs[type] = {}

            try:
                pl = extype[plugin]
            except KeyError:
                pl = extype[plugin] = ExtensionDescriptor()

            pl.addFile(k, j["blobs"][k])


class ThemesCollection(Collection):

    def plugin_name_from_file(self, file_name):

        ps = string.find(file_name, "/")
        ps = string.find(file_name, "/", ps + 1)

        if ps != -1:
            return file_name[:ps]
        else:
            return ps


    def fetch(self):

        response = urlopen(API_GITHUB_FETCHBLOB % self.theme)
        rq = response.read()
        j = loads(rq)

        for k in j["blobs"]:

            plugin = self.plugin_name_from_file(k)

            if plugin == -1:
                continue

            (type, name) = plugin.split("/")

            try:
                extype = self.extensions_descs[type]
            except KeyError:
                extype = self.extensions_descs[type] = {}

            try:
                pl = extype[name]
            except KeyError:
                pl = extype[name] = ExtensionDescriptor()

            pl.addFile(k, j["blobs"][k])

