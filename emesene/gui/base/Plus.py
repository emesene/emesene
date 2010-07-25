import re

from e3.common.XmlParser import DictObj

import gui

COLOR_MAP = (
    'ffffff','000000','00007F','009300','FF0000','7F0000','9C009C','FC7F00',
    'FFFF00','00FC00','009393','00FFFF','0000FC','FF00FF','7F7F7F','D2D2D2',
    'E7E6E4','CFCDD0','FFDEA4','FFAEB9','FFA8FF','B4B4FC','BAFBE5','C1FFA3',
    'FAFDA2','B6B4B7','A2A0A1','F9C152','FF6D66','FF62FF','6C6CFF','68FFC3',
    '8EFF67','F9FF57','858482','6E6D7B','FFA01E','F92611','FF20FF','202BFF',
    '1EFFA5','60F913','FFF813','5E6464','4B494C','D98812','EB0505','DE00DE',
    '0000D3','03CC88','59D80D','D4C804','333335','18171C','944E00','9B0008',
    '980299','01038C','01885F','389600','9A9E15','473400','4D0000','5F0162',
    '000047','06502F','1C5300','544D05')

open_tag_re = re.compile('''(.*?)\[\$?(/?)(\w+)(\=(\#?[0-9a-f]+))?\]''', re.IGNORECASE)

def parse_emotes(markup):
    '''search for emotes on markup and return a list of items with chunks of
    test and Emote instances'''
    accum = []
    for is_emote, text in gui.theme.split_smilies(markup):
        if is_emote:
            accum.append({'tag': 'img', 'src':
                gui.theme.emote_to_path(text, True), 'alt': text, 'childs': []})
        else:
            accum.append(text)

    return accum

def _msnplus_to_dict(msnplus, message_stack, do_parse_emotes=True):
    '''convert it into a dict, as the one used by XmlParser'''
    #STATUS: seems to work! (with gradients too)
    match = open_tag_re.match(msnplus)

    if not match: #only text
        if do_parse_emotes:
            parsed_markup = parse_emotes(msnplus)
        else:
            parsed_markup = [msnplus]

        message_stack.append(msnplus)
        return {'tag': 'span', 'childs': parsed_markup}

    text_before = match.group(1)
    open_ = (match.group(2) == '') #and not '/'
    tag = match.group(3)
    arg = match.group(5)

    if open_:
        if text_before.strip(): #just to avoid useless items (we could put it anyway, if we like)
            message_stack[-1]['childs'].append(text_before)

        msgdict = {'tag': tag, tag: arg, 'childs':[]}
        message_stack.append(msgdict)
    else: #closing tags
        if arg:
            start_tag = message_stack[-1][tag]
            message_stack[-1][tag] = (start_tag, arg)
        if text_before.strip(): #just to avoid useless items (we could put it anyway, if we like)
            if do_parse_emotes:
                text_before = parse_emotes(text_before)
                message_stack[-1]['childs'] += text_before
            else:
                message_stack[-1]['childs'].append(text_before)

        tag_we_re_closing = message_stack.pop() #-1

        if type(message_stack[-1]) == dict:
            message_stack[-1]['childs'].append(tag_we_re_closing)
        else:
            message_stack.append(tag_we_re_closing)

    #go recursive!
    _msnplus_to_dict(msnplus[len(match.group(0)):], message_stack)

    return {'tag': 'span', 'childs': message_stack}

def _nchars_dict(msgdict):
    '''count how many character are there'''
    nchars = 0
    for child in msgdict['childs']:
        if type(child) in (str, unicode):
            nchars += len(child)
        else:
            nchars += _nchars_dict(child)

    return nchars

#stolen from mohrtutchy: ty!
def _color_gradient(col1, col2, length):
    '''returns a list of colors. Its length is length'''
    col1 = col1.strip()
    col2 = col2.strip()

    def dec2hex(n):
        """return the hexadecimal string representation of integer n"""
        if n<16:
            return '0' + "%X" % n
        else:
            return "%X" % n

    def hex2dec(s):
        """return the integer value of a hexadecimal string s"""
        return int('0x' + s, 16)

    hex3tohex6 = lambda col: col[0] * 2 + col[1] * 2 + col[2] * 2


    if col1.startswith('#'):
        col1 = col1[1:]

    if len(col1) == 3:
        col1 = hex3tohex6(col1)

    if col2.startswith('#'):
        col2 = col2[1:]

    if len(col2) == 3:
        col2 = hex3tohex6(col2)

    R1hex=col1[:2]
    G1hex=col1[2:4]
    B1hex=col1[4:6]
    R2hex=col2[:2]
    G2hex=col2[2:4]
    B2hex=col2[4:6]
    R1dec=hex2dec(R1hex.upper())
    G1dec=hex2dec(G1hex.upper())
    B1dec=hex2dec(B1hex.upper())
    R2dec=hex2dec(R2hex.upper())
    G2dec=hex2dec(G2hex.upper())
    B2dec=hex2dec(B2hex.upper())
    stepR = (R2dec-R1dec)/(length-1.0)
    stepG = (G2dec-G1dec)/(length-1.0)
    stepB = (B2dec-B1dec)/(length-1.0)
    R = [0] * length
    R[0]=dec2hex(R1dec)
    R[length-1]=dec2hex(R2dec)
    G = [0] * length
    G[0]=dec2hex(G1dec)
    G[length-1]=dec2hex(G2dec)
    B = [0] * length
    B[0]=dec2hex(B1dec)
    B[length-1]=dec2hex(B2dec)
    for i in range(1, length-1):
        R[i] = dec2hex(int(R1dec+stepR * i))
    for i in range(1, length-1):
        G[i] = dec2hex(int(G1dec+stepG * i))
    for i in range(1, length-1):
        B[i] = dec2hex(int(B1dec+stepB * i))
    colors = [0] * length
    for i in range(0,length):
       colors[i] = R[i] + G[i] + B[i]

    return colors

def _hex_colors(msgdict):
    '''convert colors to hex'''
    if msgdict['tag']:
        tag = msgdict['tag']

        if tag in ['a', 'c']: #bg-color, color
            param = msgdict[tag]

            if type(param) == tuple: #gradient
                param1, param2 = param

                if len(param1) <= 2: #is not already hex
                    msgdict[tag] = (COLOR_MAP[int(param1)], msgdict[tag][1])
                if len(param2) <= 2: #is not already hex
                    msgdict[tag] = (msgdict[tag][0], COLOR_MAP[int(param2)])
            else: #normal color
                if len(param) <= 2: #is not already hex
                    msgdict[tag] = COLOR_MAP[int(param)]
                elif param.startswith('#'):
                    msgdict[tag] = param[1:]

    for child in msgdict['childs']:
        if child and type(child) not in (str, unicode):
            _hex_colors(child)

def _gradientify_string(msg, attr, colors):
    '''apply sequence "colors" of colors (type attr) to msg'''
    result = {'tag':'', 'childs':[]}

    for char in msg:
        color = colors.pop(0)
        result['childs'].append({'tag': attr, attr:color, 'childs':[char]})

    return result

def _gradientify(msgdict, attr=None, colors=None):
    '''apply a gradient to that msgdict'''
    if not attr:
        attr = msgdict['tag']

    if colors is None:
        param_from, param_to = msgdict[attr]
        #param_from = COLOR_MAP[int(param_from)]
        #param_to = COLOR_MAP[int(param_to)]
        lenght = _nchars_dict(msgdict)
        if (lenght != 1):
            colors = _color_gradient(param_from, param_to, lenght)
        msgdict['tag'] = ''
        del msgdict[attr]

    i = 0
    while colors and i < len(msgdict['childs']):
        this_child = msgdict['childs'][i]

        if type(this_child) in (str, unicode):
            msgdict['childs'][i] = _gradientify_string(this_child, attr, colors) #will consumate some items from colors!
        else:
            _gradientify(this_child, attr, colors)

        i += 1

def _dict_gradients(msgdict):
    '''apply gradients where needed'''
    if type(msgdict) != dict: return
    for subdict in msgdict['childs']:
        if type(subdict) == dict:
            tag = subdict['tag']
            if tag in subdict and type(subdict[tag]) == tuple:
                _gradientify(subdict)
            _dict_gradients(subdict)

def _dict_translate_tags(msgdict):
    '''translate 'a' to 'span' etc...'''
    #Work on this
    tag = msgdict['tag']
    if  tag == 'a':
        msgdict['tag'] = 'span'
        #msgdict['style'] = 'background-color: #%s;' % (msgdict['a'].upper(),) NON-PANGO
        msgdict['bgcolor'] = '#%s' % msgdict['a'].upper()
        del msgdict['a']
    elif tag == 'c':
        msgdict['tag'] = 'span'
        msgdict['color'] = '#%s' % msgdict['c'].upper()
        del msgdict['c']
    elif tag == 'img':
        pass
    elif tag not in ('span', '', 'i', 'b', 'small'):
        del msgdict[tag]
        msgdict['tag'] = ''
        msgdict['childs'].insert(0, '[%s]' % (tag, ))

    #Then go recursive!
    for child in msgdict['childs']:
        if type(child) == dict:
            _dict_translate_tags(child)

def msnplus(msnplus, do_parse_emotes=True):
    '''given a string with msn+ formatting, give a DictObj
    representing its formatting.'''
    message_stack = [{'tag':'', 'childs':[]}]
    dictlike = _msnplus_to_dict(msnplus, message_stack, do_parse_emotes)
    _hex_colors(dictlike)
    _dict_gradients(dictlike)
    _dict_translate_tags(dictlike)
    return DictObj(dictlike)

def msnplus_strip(msnplus, useless_arg=None):
    '''
    given a string with msn+ formatting, give a string with same text but
    without MSN+ markup
    @param msnplus The original string
    @param useless_arg This is actually useless, and is mantained just for
    compatibility with msnplus
    '''
    tag_re = re.compile('\[/?\w(=\d+)?\]')
    return tag_re.sub('', msnplus)

################################################################################
# WARNING: Good ol' emesene1 code from mohrtutchy, roger et. al.
# It might not be perfect or nice to see, but hell if it works, m3n.
################################################################################

colorCodes = (
'ffffff','000000','00007F','009300','FF0000','7F0000','9C009C','FC7F00',
'FFFF00','00FC00','009393','00FFFF','0000FC','FF00FF','7F7F7F','D2D2D2',
'E7E6E4','CFCDD0','FFDEA4','FFAEB9','FFA8FF','B4B4FC','BAFBE5','C1FFA3',
'FAFDA2','B6B4B7','A2A0A1','F9C152','FF6D66','FF62FF','6C6CFF','68FFC3',
'8EFF67','F9FF57','858482','6E6D7B','FFA01E','F92611','FF20FF','202BFF',
'1EFFA5','60F913','FFF813','5E6464','4B494C','D98812','EB0505','DE00DE',
'0000D3','03CC88','59D80D','D4C804','333335','18171C','944E00','9B0008',
'980299','01038C','01885F','389600','9A9E15','473400','4D0000','5F0162',
'000047','06502F','1C5300','544D05')

colorCodesHexGradient = re.compile\
    ('\[[cC]=#([0-9A-Fa-f]{6})\](.*?)\[/[cC]=#([0-9A-Fa-f]{6}|#{6})\]')
backColorCodesHexGradient = re.compile\
    ('\[[aA]=#([0-9A-Fa-f]{6})\](.*?)\[/[aA]=#([0-9A-Fa-f]{6}|#{6})\]')

tagInGradient = r'(<span[^>]*>|</span>|'\
    '\[[aA]=[0-9]{1,2}\]|\[[aA]=#[0-9A-Fa-f]{6}\]|\[/[aA]=#{7}\]|'\
    '\[/[aA]=[0-9]{1,2}\]|\[/[aA]=#[0-9A-Fa-f]{6}\])'
specialInGradient = r'(&[a-zA-Z]+\d{0,3};|\%.)'
allInGradient = r'(<span[^>]*>|</span>|'\
    '\[[aA]=[0-9]{1,2}\]|\[[aA]=#[0-9A-Fa-f]{6}\]|\[/[aA]=#{7}\]|'\
    '\[/[aA]=[0-9]{1,2}\]|\[/[aA]=#[0-9A-Fa-f]{6}\]|&[a-zA-Z]+\d{0,3};|\%.)'

openName = r'(?<=\[[cC]=|\[[aA]=)[0-9a-zA-Z]{3,6}(?=\])'
closeName = r'(?<=\[/[cC]=|\[/[aA]=)[0-9a-zA-Z]{3,6}(?=\])'
openCode = r'(?<=\[[cC]=|\[[aA]=)[0-9]{1,2}(?=\])'
closeCode = r'(?<=\[/[cC]=|\[/[aA]=)[0-9]{1,2}(?=\])'

colorIrcCode = re.compile("\xb7\$([0-9]{1,2})?,?([0-9]{1,2})?")
colorIrcCodeFG = re.compile("(?<=\xb7\$)[0-9]{1,2}")
colorIrcCodeBG = re.compile("(?<=\xb7\$,)[0-9]{1,2}")
colorIrcCodeFGBG = re.compile("(?<=\xb7\$#[0-9a-fA-F]{6},)[0-9]{1,2}")
#colorIrcCode = re.compile("\xb7\$([0-9]{1,2})?,?([0-9]{1,2})?")
colorIrcHex = re.compile("\xb7\$(#[0-9a-fA-F]{6})?,?(#[0-9a-fA-F]{6})?")
#colorIrcRGB = re.compile("\xb7\$\(([0-9]{3}),([0-9]{3}),([0-9]{3})\)")

#don't try to pack them into one regexp. please.

formatBb = {}
formatIrc = {}

tmpBb = "bius"
tmpIrc = "#&@'"

for i in range(4):
    bb = tmpBb[i]
    irc = tmpIrc[i]
    doubleCase = (bb+bb.upper(), bb+bb.upper())
    doubleIrc = (irc,irc)
    formatBb[bb] = re.compile('(\[[%s]\](.*?)\[/[%s]\])' % doubleCase)
    formatIrc[bb] = re.compile("\xb7(\%s)(.*?)(\xb7\%s|$)" % doubleIrc)
del bb, irc, doubleCase, doubleIrc

span = re.compile('(<span.*?>)|(</span>)')

colorTags = re.compile('\[[cC]=#[0-9A-Fa-f]{6}\]|\[[cC]=[0-9]{1,2}\]|'\
    '\[/[cC]\]|\[/[cC]=[0-9]{1,2}\]|\[/[cC]=#[0-9A-Fa-f]{6}\]|'\
    '\[[cC]=[0-9A-Za-z]{1,6}\]|\[/[cC]=[0-9A-Za-z]{1,6}\]')
backColorTags = re.compile('\[[aA]=#[0-9A-Fa-f]{6}\]|\[[aA]=[0-9]{1,2}\]|'\
    '\[/[aA]\]|\[/[aA]=[0-9]{1,2}\]|\[/[aA]=#[0-9A-Fa-f]{6}\]|'\
    '\[[aA]=[0-9A-Za-z]{1,6}\]|\[/[aA]=[0-9A-Za-z]{1,6}\]')
colorIrcTags = re.compile('\xb7\$[0-9]{1,2},[0-9]{1,2}|'\
    '\xb7\$[0-9]{1,2}|\xb7\$,[0-9]{1,2}|\xb7\$#[a-fA-F0-9]{6},#[a-fA-F0-9]{6}|'\
    '\xb7\$#[a-fA-F0-9]{6}|\xb7\$,#[a-fA-F0-9]{6}')
BbTags = re.compile\
    ('\[[bB]\]|\[[iI]\]|\[[uU]\]|\[[ss]\]|'\
    '\[/[bB]\]|\[/[iI]\]|\[/[uU]\]|\[/[ss]\]')
IrcTags = re.compile("\xb7\#|\xb7&[a-zA-Z]+\d{0,3};|\xb7\@|\xb70")

removeList = (colorTags,backColorTags,colorIrcTags,BbTags,IrcTags)

getTagDict = {
    'background': ('background="#%s"','background-color: #%s;'),
    'foreground': ('foreground="#%s"','color: #%s;'),
    'b': ('weight="bold"', 'font-weight: bold'), 
    'u': ('underline="single"', 'text-decoration:underline'),
    'i': ('style="italic"', 'font-style: italic'),
    's': ('strikethrough="true"', 'text-decoration: line-through'),
}

#\xc2 is for utf-8..
customStatus = re.compile("^(.*)\xa0{([^}]*)}$")

def getCustomStatus(nick):
    '''parse custom status, return tuple (nick, status)'''
    result = unicode(customStatus.search(nick),'utf8')
    if result:
        return result.groups()
    else:
        return (nick, '')

class MsnPlusMarkupMohrtutchy:
    def __init__( self ):
        self.isHtml = False

    def removeMarkup( self, text ):
        '''remove the [b][/b] etc markup for pango and html markup'''

        # already unicode here
        text = unicode(text,'utf8')

        all = removeList 

        for i in all:
            text = re.sub( i, '', text)
        all =tuple(formatBb.values() + formatIrc.values())
        for i in all:
            text = re.sub( i, lambda x:x.groups()[1], text)
             
        text = re.sub( colorIrcCode, '', text )
        return text

    def replaceMarkup( self, text ):

        '''replace the [b][/b] etc markup for pango and html markup'''

        text = unicode(text,'utf8')

        text = text.replace\
            ('\xc2\xb7&amp;','\xc2\xb7&').replace('\xc2\xb7&quot;','\xc2\xb7"')\
            .replace('\xc2\xb7&apos;','\xc2\xb7\'')
            #@ROGER: i hate this, i hate it too..
            #@ROGER: me too... mohrtutchy
        
        self.more = 0
        self.backgroundColor = self.frontColor = ''
                
        self.openSpan = None
        def q(dictionary, tag, text): #quick handler
            def handler(x):
                return self.getTag({tag: ''}, x.groups()[1])
            return re.sub(dictionary[tag], handler, text)

        text = re.sub('\xb70','',text)

        for tag in 'bius':
            text = q(formatBb, tag, text)
            text = q(formatIrc, tag, text)

        text = re.sub( openName, self.nameToHex, text)
        text = re.sub( closeName, self.nameToHex, text)
        text = re.sub( openCode, self.codeToHex, text)
        text = re.sub( closeCode, self.codeToHex, text)
        text = re.sub( colorIrcCodeFG, self.codeToHex, text)
        text = re.sub( colorIrcCodeBG, self.codeToHex, text)
        text = re.sub( colorIrcCodeFGBG, self.codeToHex, text)

        # I know these two lines are not very nice, I beg you pardon :P
        text = re.sub( '\[/[cC]\]', '[/c=#######]',text)
        text = re.sub( '\[/[aA]\]', '[/a=#######]',text)
        
        text = re.sub( colorCodesHexGradient, self.hexToTagGrad, text )
        text = re.sub( backColorCodesHexGradient, self.bHexToTagGrad, text )

        text = re.sub( '\[[cC]=#[0-9a-fA-F]{6}\]|'\
                '\[/[cC]=#[0-9a-fA-F]{6}\]|\[/c=#######\]','',text)
        text = re.sub( '\[[aA]=#[0-9a-fA-F]{6}\]|'\
                '\[/[aA]=#[0-9a-fA-F]{6}\]|\[/a=#######\]','',text)
        
        text = re.sub( colorIrcHex, self.ircHexToTag, text ) 

        if self.openSpan != None:
            #TODO: fix this with msgplus codes, '&#173;'?
            pos = text.find("no-more-color")
            if pos != -1:
                text = text.replace("no-more-color",'</span>')
            else:
                text += '</span>'

        return text.replace('\xc2\xb7&','\xc2\xb7&amp;').replace\
            ('\xc2\xb7"','\xc2\xb7&quot;')\
            .replace('\xc2\xb7\'','\xc2\xb7&apos;')
        

    def codeToHex( self, data ):
        code=data.group()
        if int(code) < len(colorCodes):
            hex = '#'+colorCodes[int(code)].lower()
            return hex
        elif int(code) > 67 and int(code) < 100:
            return '#000000'
        else:
            return code

    def nameToHex( self, data ):
        code=data.group()
        if code.lower() == 'white':
            return '#ffffff'
        elif code.lower() == 'black':
            return '#000000'
        elif code.lower() == 'marine':
            return '#00007F'
        elif code.lower() == 'green':
            return '#009300'
        elif code.lower() == 'red':
            return '#FF0000'
        elif code.lower() == 'brown':
            return '#7F0000'
        elif code.lower() == 'purple':
            return '#9C009C'
        elif code.lower() == 'orange' :
            return '#FC7F00'
        elif code.lower() == 'yellow':
            return '#FFFF00'
        elif code.lower() == 'lime':
            return '#00FC00'
        elif code.lower() == 'teal' :
            return '#009393'
        elif code.lower() == 'aqua' :
            return '#00FFFF'
        elif code.lower() == 'blue' :
            return '#0000FC'
        elif code.lower() == 'pink' :
            return '#FF00FF'
        elif code.lower() == 'gray' :
            return '#7F7F7F'
        elif code.lower() == 'silver':
            return '#D2D2D2'
        elif code.lower() == 'mohr':
            return '#ff00de'
        elif code.lower() == 'c10ud' :
            return '#313373'
        else:
            return code
        
    def ircHexToTag( self, data ):
        text = ''
        color1, color2 = data.groups()
        try:
            color1 = color1[1:]
        except:
            pass
        try:
            color2 = color2[1:]
        except:
            pass

        if self.frontColor != '' and color1 == None:
            color1 = self.frontColor

        if self.backgroundColor != '' and  color2 == None:
            color2 = self.backgroundColor
        
        self.frontColor = color1
        self.backgroundColor = color2
        
        try:
            if color1 != None and color2 != None:
                fghex = color1.lower()
                bghex = color2.lower()
                text = self.getTag({'foreground': fghex, 'background': bghex},
                    None)

            elif color1 != None:
                fghex = color1.lower()
                text = self.getTag({'foreground': fghex}, None)
                        
            elif color2 != None:
                bghex = color2.lower()
                text = self.getTag({'background': bghex}, None)
        except IndexError:
            # i'm giving up. i can't deal with tuples. i fail
            pass
                    
        if self.openSpan != None:
            text = '</span>' + text

        if text:
            self.openSpan = True
            return text
        
    def dec2hex(self, n):
        """return the hexadecimal string representation of integer n"""
        if n<16:
            return '0' + "%X" % n
        else:
            return "%X" % n
     
    def hex2dec(self, s):
        """return the integer value of a hexadecimal string s"""
        return int('0x'+s, 16)

    def gradient(self, col1,col2,length):
        R1hex=col1[:2]
        G1hex=col1[2:4]
        B1hex=col1[4:6]
        R2hex=col2[:2]
        G2hex=col2[2:4]
        B2hex=col2[4:6]
        R1dec=self.hex2dec(R1hex.upper())
        G1dec=self.hex2dec(G1hex.upper())
        B1dec=self.hex2dec(B1hex.upper())
        R2dec=self.hex2dec(R2hex.upper())
        G2dec=self.hex2dec(G2hex.upper())
        B2dec=self.hex2dec(B2hex.upper())
        stepR =((float(R2dec)-float(R1dec))/(float(length)-float(1)))
        stepG =((float(G2dec)-float(G1dec))/(float(length)-float(1)))
        stepB =((float(B2dec)-float(B1dec))/(float(length)-float(1)))
        R = [0] * length 
        R[0]=self.dec2hex(R1dec)
        R[length-1]=self.dec2hex(R2dec)
        G = [0] * length 
        G[0]=self.dec2hex(G1dec)
        G[length-1]=self.dec2hex(G2dec)
        B = [0] * length 
        B[0]=self.dec2hex(B1dec)
        B[length-1]=self.dec2hex(B2dec)
        for i in range(1, length-1):
            R[i] = self.dec2hex(int(R1dec+stepR * i))
        for i in range(1, length-1):
            G[i] = self.dec2hex(int(G1dec+stepG * i))
        for i in range(1, length-1):
            B[i] = self.dec2hex(int(B1dec+stepB * i))
        colors = [0] * length
        for i in range(0,length):
           colors[i] = R[i] + G[i] + B[i]
        return colors

    def longTagged( self, colors, text):
        textSplit=filter(None,re.split(allInGradient,text))
        k=0
        for j in range(0,len(textSplit)):
            if len(re.findall(tagInGradient,textSplit[j])) == 0:
                tagged=''
                if len(re.findall(specialInGradient,textSplit[j])) == 0:
                    for i in range(0,len(textSplit[j])):
                        tagged=tagged + self.getTag\
                                ({'foreground': colors[k]},textSplit[j][i])
                        k=k+1
                else:
                    tagged=tagged + self.getTag\
                            ({'foreground': colors[k]},textSplit[j])
                    k=k+1
                textSplit[j]=tagged
        textn=''
        for j in range(0,len(textSplit)):
            textn=textn+textSplit[j]
        return textn

    def blongTagged( self, colors, text):
        textSplit=filter(None,re.split(allInGradient,text))
        k=0
        for j in range(0,len(textSplit)):
            if len(re.findall(tagInGradient,textSplit[j])) == 0:
                tagged=''
                if len(re.findall(specialInGradient,textSplit[j])) == 0:
                    for i in range(0,len(textSplit[j])):
                        tagged=tagged + self.getTag\
                                ({'background': colors[k]},textSplit[j][i])
                        k=k+1
                else:
                    tagged=tagged + self.getTag\
                            ({'background': colors[k]},textSplit[j])
                    k=k+1
                textSplit[j]=tagged
        textn=''
        for j in range(0,len(textSplit)):
            textn=textn+textSplit[j]
        return textn
  
    def hexToTagGrad( self, data ):
        color1 = data.group(1)
        text = data.group(2)
        text = re.sub(colorTags,'',text)
        text = re.sub(colorIrcTags,'',text)
        color2 = data.group(3)
        if color2 == '######' or color2 == color1:
            return self.getTag({'foreground': color1}, text)
        else:
            length = len(re.sub(specialInGradient,'a',\
                    re.sub(tagInGradient,'',text)))
            if length>1:
                colors=self.gradient(color1,color2,length)
                tagged = self.longTagged( colors, text)
                return tagged
            else:
                return text
    
    def bHexToTagGrad( self, data ):
        color1 = data.group(1)
        text = data.group(2)
        text = re.sub(backColorTags,'',text)
        text = re.sub(colorIrcTags,'',text)
        color2 = data.group(3)
        if color2 == '######' or color2 == color1:
            return self.getTag({'background': color1}, text)
        else:
            length = len(re.sub(specialInGradient,'a',\
                    re.sub(tagInGradient,'',text)))
            if length>1:
                colors=self.gradient(color1,color2,length)
                tagged = self.blongTagged( colors, text)
                return tagged
            else:
                return text
    
    def RGBToHTMLColor( self, rgb_tuple ):
        '''convert an (R, G, B) tuple to #RRGGBB'''
        return '#%02x%02x%02x' % rgb_tuple
       
    def HTMLColorToRGB( self, colorstring ):
        '''convert #RRGGBB to an (R, G, B) tuple'''
        colorstring = colorstring.strip()
        if colorstring.startswith('#'): 
            colorstring = colorstring[1:]
            
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return (r, g, b)

    def getTag( self, attrdict, text ):
        attrs = []
        for key in attrdict.keys():
            if key in getTagDict:
                attr = getTagDict[key][int(self.isHtml)]
            attr = attr.replace("%s", attrdict[key])
            attrs.append(attr)

        if self.isHtml:
            tagattr = 'style="'
            for attr in attrs:
                tagattr += attr
            tagattr += '"'
        else:
            tagattr = ''
            for attr in attrs:
                tagattr += attr
        
        if text == None:
            return '<span ' + tagattr + '>'
        else:
            return '<span ' + tagattr + '>' + text + '</span>'

if __name__ == '__main__':
    nick = '''[a=#f0Ff00]foo[b]bar[/b] rulez, [i]ain't it?[/i][/A] we say'''
    nick = '''[M]Implement[i][!][]ing[/i] [c=2]MS[N][/c] [c=3]PLUS[/c]'''

    print 'NICK', nick

    dictlike = msnplus(nick)
    print 'DICT', dictlike
    print 'XML', dictlike.to_xml()


    import sys
    sys.path.append('../..')
    from gui.gtkui import RichBuffer
    import gtk

    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    textview = gtk.TextView()
    buff = RichBuffer.RichBuffer()
    textview.set_buffer(buff)
    #window.add(textview)
    #buff._put_formatted(DictObj(dictlike))
    buff.put_formatted(dictlike.to_xml())

    label = gtk.Label()
    label.set_markup(dictlike.to_xml())

    window.add(label)

    window.show_all()
    gtk.main()

