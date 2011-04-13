# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import re
import gobject

import xml.sax.saxutils
import gui

dic = {
    '\"'    :    '&quot;',
    '\''    :    '&apos;'
}

dic_inv = {
    '&quot;'    :'\"',
    '&apos;'    :'\''
}

def escape(string):
    return xml.sax.saxutils.escape(string, dic)

def unescape(string):
    return xml.sax.saxutils.unescape(string, dic_inv)

# constants
TAGS_NONE = 0
TAGS_PANGO = 1
TAGS_HTML = 2

# "data types" parse text for an specific target

class DefaultDataType( object ):
    tags = TAGS_NONE

    def __init__( self, text, parser ):
        self.parser = parser
        self.text = text

    def get( self, escaped=True ):
        data = ''
        for item in self.parser.parse( self, self.text ):
            if escaped:
                data += str(item)
            else:
                data += unescape(str(item))
        return data

    def parseAll( self ):
        data = ''
        for item in self.text:
            try:
                data += item.getHtml()
            except:
                data += str( item )
        return data

    def getDataType( self ):
        return 'default'

class PangoDataType( DefaultDataType ):
    '''This returns a list with strings and pixbufs'''
    tags = TAGS_PANGO

    def __init__( self, text, parser ):
        DefaultDataType.__init__( self, text, parser )
        self.parser = parser
        self.text = text
        self.regex = re.compile("<span([^>]*)>(.*)$")
        self.tagsopen = []

    def getDataType( self ):
        return 'pango'

    def get( self, smileys=True, cache={} ):
        '''returns list, not a string!'''
        ret = []
        tags = list()
        closed = ""
        opened = ""
        for item in self.parser.parse( self, self.text ):
            if type(item) == Url:
                item = item.__str__() # don't parse urls
            if type(item) in (str, unicode, Url):
                if item != "" and item != "</span>":
                    item = opened + item
                    aux = item
                    pos = aux.find("[$")
                    while pos != -1:
                        index = pos+2
                        found = aux[index]
                        if found == "b":
                            tags.append("b")
                        elif found == "i":
                            tags.append("i")
                        elif found == "s":
                            tags.append("small")
                        elif found == "/":
                            if len(tags) > 0:
                                tags.pop()
                        aux = aux[index+1:]
                        pos = aux.find("[$")
                    opened = ""
                    ret = self.handystringhandler( ret, item )

            elif type(item) == Smiley:
                if not smileys:
                    ret = self.addstr(ret, str(item))
                    continue
                if item.smiley in cache:
                    item.pixbuf = cache[ item.smiley ]
                else:
                    item.pixbuf = item.getPixbuf(False)
                while len(tags) > 0:
                    tag = tags.pop()
                    closed = closed+"[$/"+tag+"]"
                    opened = "[$"+tag+"]"+opened
                self.addstr(ret, closed)
                closed = ""
                ret.append(item)
        return [self.fix(i) for i in ret]

    def addstr( self, ret, string ):
        '''adds a string to the last item if possible'''
        if len(ret) > 0 and type(ret[-1]) == str and ret[-1] != '\n':
            ret[-1] += str(string)
        else:
            ret.append(str(string))
        return ret

    def handystringhandler( self, ret, item ):
        '''separates a string by the \n if needed'''
        if type(item) == Url:
            item = str(item)
        if str(item).find('\n') != -1:
            olditem, item = str(item).split('\n', 1)
            ret = self.addstr(ret, olditem)
            ret.append('\n')
        ret = self.addstr(ret, item)
        return ret

    def fix(self, data):
        '''close tags before a smiley and reopen after it'''

        if type(data) == str:
            pre = ''.join(self.tagsopen)
            self.tagsopen = []

            # reopen tags after our personal tags
            personaltags = ["[$b]", "[$small]", "[$i]"]
            aux = data
            leave = False
            front = ""
            while not leave:
                removeFront = False
                for x in personaltags:
                    removeFront = removeFront or aux.startswith(x)
                if removeFront:
                    pos = aux.find("]")+1
                    front = front+aux[:pos]
                    aux = aux[pos:]
                else:
                    leave = True
            data = self.regex.sub(self.fixhandler, pre+aux)
            data = front + data
            
            closedTags = data.count('</span>')
            if closedTags > 0:
                self.tagsopen = self.tagsopen[:-closedTags]

            #close tags before our personal tags
            personaltags = ["[$/b]", "[$/small]", "[$/i]"]
            aux = data
            leave = False
            tail = ""
            while not leave:
                pos = aux.rfind("[$/")
                aux2 = aux[pos:]
                if aux2 in personaltags:
                    aux = aux[:pos]
                    tail = aux2 + tail
                else:
                    leave = True
            data = aux + ('</span>' * len(self.tagsopen)) + tail

        return data

    def fixhandler(self, data):
        '''self.regex.sub handler'''
        group0, group1 = data.groups()
        group1 = self.regex.sub(self.fixhandler, group1)
        self.tagsopen.append('<span%s>' % group0)
        return '<span%s>%s' % (group0,group1)


class UserListDataType( PangoDataType ):
    '''This returns a list with strings and pixbufs'''
    tags = TAGS_PANGO

    def __init__( self, text, parser ):
        PangoDataType.__init__( self, text, parser )

    def getDataType( self ):
        return 'userlist'

    def get( self, smileys=True, cache={} ):
        '''returns list, not a string!'''
        ret = []

        # unpack the tuple :D
        template = self.text[0]
        params = self.text[1:]
        
        # pseudo format()
        template = template.split("%s")

        for part in params:
            ret = self.handystringhandler(ret, template.pop(0))
            ret = self.multipart_parse(ret, part, smileys, cache)

        if len(template) > 0:
            ret = self.handystringhandler(ret, template.pop(0))

        return [self.fix(i) for i in ret]

    ###
    # EVERYTHING (!) BELOW THIS COMMENT IS THE RESULT
    # OF REALLY HEAVY CODE REUTILISATION
    ###
    # (inside the class, i mean)

    def multipart_parse( self, ret, part, smileys, cache ):
        '''sends a chunk to the parser, adds to ret'''
        for item in self.parser.parse( self, part ):
            if type(item) in (str, unicode, Url):
                ret = self.handystringhandler( ret, item )

            elif type(item) == Smiley:
                if not smileys:
                    ret = self.addstr(ret, str(item))
                    continue
                if item.smiley in cache:
                    item.pixbuf = cache[ item.smiley ]
                else:
                    item.pixbuf = item.getPixbuf(False)
                ret.append(item)
        return ret

class ConversationDataType( DefaultDataType ):
    tags = TAGS_HTML

    def __init__( self, text, parser ):
        DefaultDataType.__init__( self, text, parser )
        self.conversation = None
        self.ink = None
        self.username = None

    def subOCE( self, data ):
        ce = data.groups()[0]
        msnOM = self.conversation.switchboard.msn.getMsnObjectsManager()
        filename = msnOM.getById(unescape(ce)).filename.replace("%", "%25")
        if os.name == 'posix':
            return '<img src="file://%s" alt="%s"/>' % (filename, ce)
        else:
            return '<img src="file://localhost/%s" alt="%s"/>' % (filename, ce)

    def subICE( self, data ):
        ce = data.groups()[0]
        customEmoticons = self.conversation.customEmoticons.get( self.username )
        return '<object type="application/x-emesene-emoticon" class="%s" ' \
            'data="%s"></object>' % (customEmoticons[unescape(ce)], ce)

    def get( self, urls=True, smileys=True ):
        data = ''
        cePattern=''
        if self.ink:
            return '<object type="application/x-emesene-ink" class="%s">' \
                '</object>' % (self.text,)

        if smileys == True and self.conversation:
            if self.username == self.conversation.switchboard.user:
                sub = self.subOCE
                msnOM = self.conversation.switchboard.msn.getMsnObjectsManager()
                for ce in msnOM.getIds():
                    cePattern += re.escape(escape(ce)) + '|'
            else:
                sub = self.subICE
                customEmoticons = self.conversation.customEmoticons\
                    .get( self.username )
                for ce in customEmoticons:
                    cePattern += re.escape(escape(ce)) + '|'

        text = self.text

        for item in self.parser.parse( self, text ):
            if type( item ) in (str, unicode):
                if cePattern!= '':
                # this hack to the regexp fixes the empty messages bug.
                # thanks to dx for pointing out the line where shit happened
                # and to me (c10ud) for having the revelation (!) from
                # python re manuals. 
                # p.s. currently handled: " ' softhyphen & > <
                #                                         XOXO RegExp Girl
                    item = re.sub(\
                    '(?<!&quot)(?<!&apos)(?<!&#173)(?<!&amp)(?<!&gt)(?<!&lt)(' \
                    + cePattern[:-1] + ')', sub, item )
                data += item
            elif type(item) == Url:
                if urls:
                    data += item.getHtml()
                else:
                    data += str( item )
            elif type(item) == Smiley:
                if smileys:
                    data += item.getHtml()
                else:
                    data += str( item )

        return data

    def setConversation( self, conversation ):
        self.conversation = conversation

    def setInk( self, value ):
        self.ink = True

    def setUser( self, username ):
        if username:
            self.username = username.lower()

    def getDataType( self ):
        return 'conversation'


class Smiley(object):
    ''' this class represents a smiley in a pango markup '''
    def __init__( self, smiley, theme ):
        self.smiley = smiley
        self.pixbuf = None
        self.scaled = False

    def getHtml( self ):
        if gui.theme.emote_to_path(self.smiley) == None:
            print _('Can\'t find the smiley %s')%self.smiley
            return escape( self.smiley )

        path = gui.theme.emote_to_path(self.smiley, True).replace("%", "%25")
        if path.startswith('/'):
            url = 'file://' + path
        else:
            url = 'file://localhost/' + path # Windows
        return '<img src="%s" alt="%s"/>' % (url, escape(self.smiley))

    def getPixbuf(self, anim=True):
        path = gui.theme.emote_to_path(self.smiley, remove_protocol=True)
        pix = gui.gtkui.utils.safe_gtk_pixbuf_load(path, size=None, animated=anim)
        return pix
        
    def __str__( self ):
        return escape(self.smiley)

    def __repr__(self):
        return '<smiley ' + self.smiley + '>'

    def scale( self, cache, size ):
        if self.scaled: return
        if self.smiley in cache:
            self.pixbuf = cache[self.smiley]
        else:
            if not self.pixbuf:
                self.pixbuf = self.getPixbuf(False)
            self.pixbuf = self.pixbuf.scale_simple(size, size, 2) #bilinear
            self.scaled = True
            cache[self.smiley] = self.pixbuf

class Url(object):
    def __init__( self, url ):
        self.url = url

    def getHtml( self ):
        href = self.url
        if self.url[:4] == 'www.':
            href  = 'http://'+self.url
        elif self.url[:4] == 'ftp.':
            href  = 'ftp://'+self.url
        return '<a href="%s">%s</a>' % (escape(href), escape(self.url))

    def __str__(self):
        return escape(self.url)

    def __repr__(self):
        return '<url ' + self.url + '>'

# the unified parser class itself

class UnifiedParser( gobject.GObject ):
    __gsignals__ = {
        #see the FilterData class docstring
        'filter' : (gobject.SIGNAL_RUN_LAST, str, [gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT] ),
        }

    custompatterns = {} # {name: (regex, handler)}

    def __init__(self):
        gobject.GObject.__init__( self )
        self.urlsPattern = "(?P<url>(?<![A-Za-z0-9])((?:https?\:\/\/|ftp\:\/\/|www\.|ftp\.)(?:\S*[;:~]?)))"
        self.smileyPattern=''
        for smiley in gui.theme.EMOTES.keys():
            self.smileyPattern += re.escape( smiley ) + '|'
        self.smileyPattern = '(?P<smiley>'+self.smileyPattern[:-1]+')'

        self.recompileRegex()

    def getParser(self, text, dataType=DefaultDataType):
        return dataType( text, self )

    def parse(self, datatype, text):
        list = []
        def handler( data ):
            group = data.groupdict()
            if group['smiley']:
                list.append( Smiley(group['smiley'], gui.theme.theme_path) )
            elif group['url']:
                pos = group['url'].find("[$")
                if pos != -1:
                    list.append(Url(group['url'][:pos]))
                    list.append(group['url'][pos:])
                else:
                    list.append( Url( group['url'] ) )
            elif group['other']:
                other = escape(str(group['other']))
                if len(list)>0 and isinstance(list[-1], str):
                    list[-1] += other
                else:
                    list.append(other)
        self.reALL.sub( handler, text )
        data = FilterData( list=list )
        self.emit( 'filter', datatype, data )
        return data.list

    def recompileRegex( self ):
        custom = ''
        for name in self.custompatterns.keys():
            self.custompatterns[name][0]
            custom += '(?P<' + name + '>' + self.custompatterns[name][0] + ')|'
        pattern = self.urlsPattern + '|' + \
                  self.smileyPattern + '|' + \
                  custom + '(?P<other>.)'
        self.reALL = re.compile( pattern,re.DOTALL )

# filters in gobject! yay!

class FilterData(object):
    '''A class to hold data that can be modified even in
    gobject signal handlers. That makes them "filters"'''

    def __init__( self, **kw ):
        for key in kw.keys():
            setattr(self, key, kw[key])

    def serialize( self, list ):
        '''Converts a list into a format string and a list of objects
        returns (str, list), where the second list is the object list'''

        format = ''
        objects = []

        for item in list:
            if type(item) in (str, unicode):
                # string, just escape and add it
                format += str(item).replace("%", "%%")
            else:
                # object, represented with a "%s" in the format string
                format += '%s'
                objects.append(item)
        return (format, objects)

    def deserialize( self, format, objects ):
        '''Converts a format string and a list of objects into a list
        returns list [str, obj, str, ...]'''

        list = []
        format = str(format)

        while len(format) > 0:
            # find the next object
            pos = format.find("%s")

            if pos == -1:
                #no more objects in string
                list.append(format.replace("%%","%"))
                return list

            if pos != 0 and format[pos-1] == "%":
                # escaped %, include it in text
                text, format = format[:pos+2], format[pos+2:]
                object = None
            else:
                # real object, exclude it from text
                text, format = format[:pos], format[pos+2:]
                object = objects.pop(0)

            # unescape % from deserialized string
            list.append(text.replace("%%","%"))
            if object:
                list.append(object)

        return list

if __name__=='__main__':
    import Theme

    theme = Theme.Theme('')
    parser = UnifiedParser( theme )
    #data = ':D :o :P http://someurl.com/~das/:Dx/index.od?asd=asd&asd [b]test[/b] :D <:o)(G)(@)")'
    data = '") <tag> [b][/b] %s % omg omg'
    print "Conversation:"
    print '  ', parser.getParser( data, ConversationDataType ).get()
    print "UserList:"
    print '  ', parser.getParser( ('%s',data), UserListDataType ).get()
    print "Default:"
    print '  ', parser.getParser( data ).get()
