# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009-2010 Riccardo (C10uD) <c10ud.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import e3
from e3.base import status

import papyon

STATUS_PAPY_TO_E3 = { \
    papyon.Presence.ONLINE : status.ONLINE,
    papyon.Presence.BUSY : status.BUSY,
    papyon.Presence.IDLE : status.IDLE,
    papyon.Presence.AWAY : status.AWAY,
    papyon.Presence.BE_RIGHT_BACK : status.AWAY,
    papyon.Presence.ON_THE_PHONE : status.AWAY,
    papyon.Presence.OUT_TO_LUNCH : status.AWAY,
    papyon.Presence.INVISIBLE : status.OFFLINE,
    papyon.Presence.OFFLINE : status.OFFLINE}
    
STATUS_E3_TO_PAPY = { \
    status.ONLINE : papyon.Presence.ONLINE,
    status.BUSY : papyon.Presence.BUSY,
    status.IDLE : papyon.Presence.IDLE,
    status.AWAY : papyon.Presence.AWAY,
    status.OFFLINE : papyon.Presence.INVISIBLE}
    
def formatting_papy_to_e3(format = papyon.TextFormat(), size_=None):
    font = format.font
    color = e3.base.Color.from_hex('#' + str(format.color))
    bold = format.style & papyon.TextFormat.BOLD == papyon.TextFormat.BOLD
    italic = format.style & papyon.TextFormat.ITALIC == papyon.TextFormat.ITALIC
    underline = format.style & papyon.TextFormat.UNDERLINE == papyon.TextFormat.UNDERLINE
    strike = format.style & papyon.TextFormat.STRIKETHROUGH == papyon.TextFormat.STRIKETHROUGH
    size = size_
    return e3.base.Style(font, color, bold, italic, underline, strike, size)
    
def formatting_e3_to_papy(format = e3.base.Style()):
    font = format.font
    style = 0
    if format.bold: style |= papyon.TextFormat.BOLD
    if format.italic: style |= papyon.TextFormat.ITALIC
    if format.underline: style |= papyon.TextFormat.UNDERLINE
    if format.strike: style |= papyon.TextFormat.STRIKETHROUGH
    color = format.color.to_hex()
    charset = papyon.TextFormat.DEFAULT_CHARSET # wtf
    family = papyon.TextFormat.FF_DONTCARE # wtf/2
    pitch = papyon.TextFormat.DEFAULT_PITCH # wtf/3
    right_alignment = False # wtf/4
    
    return papyon.TextFormat(font, style, color, charset, family, pitch, \
        right_alignment)

def get_proxies():
    import urllib
    proxies = urllib.getproxies()
    result = {}
    if 'https' not in proxies and \
            'http' in proxies:
        url = proxies['http'].replace("http://", "https://")
        result['https'] = papyon.Proxy(url)
    for type, url in proxies.items():
        if type == 'no': continue
        if type == 'https' and url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        result[type] = papyon.Proxy(url)
    return result
