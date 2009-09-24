# this module will include a parser for all the markups that will
# convert it into a restricted subset of xhtml
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

def escape(string_):
    '''replace the values on dic keys with the values'''
    return xml.sax.saxutils.escape(string_, dic)

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, dic_inv)

def parse_emotes(message):
    '''parser the emotes in a message, return a string with img tags
    for the emotes acording to the theme'''

    chunks = [message]
    shortcuts = gui.Theme.EMOTES.keys()
    temp = []

    while len(shortcuts) > 0:
        shortcut = shortcuts.pop()
        temp = []

        for chunk in chunks:
            parts = chunk.split(shortcut)

            if len(parts) > 1:
                path = gui.theme.emote_to_path(shortcut)
                tag = '<img src="%s" alt="%s"/>' % (path, shortcut)

                for part in parts:
                    temp.append(part)
                    temp.append(tag)

                temp.pop()
            else:
                temp.append(chunk)

        chunks = temp

    return ''.join(chunks)

def parse_custom_emotes(message, cedict):
    '''parser the custom emotes in a message, return a string with img tags
       for the emotes
    '''
 
    chunks = [message]
    shortcuts = cedict.keys()
    temp = []
 
    while len(shortcuts) > 0:
        shortcut = shortcuts.pop()
        temp = []
        for chunk in chunks:
            parts = chunk.split(shortcut)
 
            if len(parts) > 1:
                path = cedict[shortcut]
                tag = '<img src="%s" alt="%s"/>' % (path, shortcut)
                for part in parts:
                    temp.append(part)
                    temp.append(tag)
 
                temp.pop()
            else:
                temp.append(chunk)
 
        chunks = temp
 
    return ''.join(chunks)

