# this module will include a parser for all the markups that will
# convert it into a restricted subset of xhtml
import os
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

def parse_emotes(message, cedict={}):
    '''parser the emotes in a message, return a string with img tags
    for the emotes acording to the theme'''

    chunks = [message]
    shortcuts = gui.Theme.EMOTES.keys()
    if cedict is not None:
        shortcuts.extend(cedict.keys())
    temp = []

    while len(shortcuts) > 0:
        shortcut = shortcuts.pop()
        temp = []

        for chunk in chunks:
            parts = chunk.split(shortcut)

            if len(parts) > 1:
                if shortcut in gui.Theme.EMOTES.keys():
                    path = gui.theme.emote_to_path(shortcut)
                else:
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


def replace_emotes(msgtext, cedict={}, cedir=None):
    '''replace emotes with img tags to the images'''
    shortcuts = gui.Theme.EMOTES.keys()
    if cedict is not None:
        shortcuts.extend(cedict.keys())
    for shortcut in shortcuts:
        if shortcut in msgtext:
            if shortcut in gui.Theme.EMOTES.keys():
                path = gui.theme.emote_to_path(shortcut)
            else:
                path = os.path.join(cedir, cedict[shortcut])

            if path is not None:
                imgtag = '<img src="%s" alt="%s"/>' % (path, shortcut)
                msgtext = msgtext.replace(shortcut, imgtag)

    return msgtext

def get_custom_emotes(message, cedict={}):
    ''' returns a list with the shortcuts of the 
        custom emoticons present in the message
        celist comes from cache '''
    chunks = [message]
    l = []    
    if cedict is None:
        return l
    shortcuts = cedict.keys()
    while len(shortcuts) > 0:
        shortcut = shortcuts.pop()

        for chunk in chunks:
            parts = chunk.split(shortcut)

            if len(parts) > 1:
                l.append(shortcut)
    return l

