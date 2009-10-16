import re
import pprint

from XmlParser import DictObj

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


open_tag_re = re.compile('''(.*?)\[(/?)(\w)(\=(\#?[0-9a-f]+))?\]''', re.IGNORECASE)
message_stack = [{'tag':'', 'childs':[]}]
def _msnplus_to_dict(msnplus):
    '''convert it into a dict, as the one used by XmlParser'''
    #STATUS: seems to work! (with gradients too)
    match = open_tag_re.match(msnplus)

    if not match: #only text
        message_stack.append(msnplus)
        return {'tag':'span', 'childs':[msnplus]}

    text_before = match.group(1)
    open_ = (match.group(2) == '') #and not '/'
    tag = match.group(3)
    arg = match.group(5)
    if open_:
        if text_before.strip(): #just to avoid useless items (we could put it anyway, if we like)
            message_stack[-1]['childs'].append(text_before)

        msgdict = {'tag': tag, tag:arg, 'childs':[]}
        message_stack.append(msgdict)
    else: #closing tags
        if arg:
            start_tag = message_stack[-1][tag]
            message_stack[-1][tag] = (start_tag, arg)
        if text_before.strip(): #just to avoid useless items (we could put it anyway, if we like)
            message_stack[-1]['childs'].append(text_before)
        tag_we_re_closing = message_stack.pop() #-1

        if type(message_stack[-1]) == dict:
            message_stack[-1]['childs'].append(tag_we_re_closing)
        else:
            message_stack.append(tag_we_re_closing)

    #go recursive!
    _msnplus_to_dict(msnplus[len(match.group(0)):])

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
        if s == '':
            print 'colores:', col1, col2, s
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
    stepR =((float(R2dec)-float(R1dec))/(float(length)-float(1)))
    stepG =((float(G2dec)-float(G1dec))/(float(length)-float(1)))
    stepB =((float(B2dec)-float(B1dec))/(float(length)-float(1)))
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
        colors = _color_gradient(param_from, param_to, _nchars_dict(msgdict))
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
    elif tag not in ('span', '', 'i', 'b'):
        del msgdict[tag]
        msgdict['tag'] = ''
        msgdict['childs'].insert(0, '[%s]' % (tag, ))

    #Then go recursive!
    for child in msgdict['childs']:
        if type(child) == dict:
            _dict_translate_tags(child)

def msnplus(msnplus):
    '''given a string with msn+ formatting, give a DictObj
    representing its formatting.'''
    global message_stack
    dictlike = _msnplus_to_dict(msnplus)
    _hex_colors(dictlike)
    _dict_gradients(dictlike)
    _dict_translate_tags(dictlike)
    message_stack = [{'tag':'', 'childs':[]}]
    return DictObj(dictlike)

def msnplus_strip(msnplus):
    '''given a string with msn+ formatting, give a string with same text but
    without MSN+ markup'''
    tag_re = re.compile('\[/?\w(=\d+)?\]')
    return tag_re.sub('', msnplus)

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

