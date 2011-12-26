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

import MessageFormatter
import threading

def add_style_to_message(text, stl, escape=True):
    '''add the style in a xhtml like syntax to text'''
    if escape:
        text = MessageFormatter.escape(text)

    if stl is None:
        return text

    style_start = ''
    style_end = ''
    style = 'color: #' + stl.color.to_hex() + '; '

    if stl.bold:
        style_start = style_start + '<b>'
        style_end = '</b>' + style_end

    if stl.italic:
        style_start = style_start + '<i>'
        style_end = '</i>' + style_end

    if stl.underline:
        style_start = style_start + '<u>'
        style_end = '</u>' + style_end

    if stl.strike:
        style_start = style_start + '<s>'
        style_end = '</s>' + style_end

    if stl.font:
        style += "font-family: %s; " % (stl.font, )

    style_start += '<span style="%s">' % (style, )
    style_end = '</span>' + style_end


    return style_start + text + style_end

class PercentDone(object):

        def __init__(self, total):
                self.__total = total
                self.__current = 0

        @property
        def current(self):
                return self.__current

        @property
        def total(self):
                return self.__total

        @total.setter
        def total(self, total):
                self.__total = total

        def notify(self, q):
                aux = (int)((q/self.__total) * 100.0)
                if aux == self.__current:
                    changed = False
                else:
                    changed = True

                self.__current = aux
                return changed


class AsyncAction(threading.Thread):

    def __init__(self, callback, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self._result = None
        self._callback = callback
        self._func = func
        self._args = args
        self._kwargs = kwargs

        self.start()

    def run(self):
        result = self._func(*self._args, **self._kwargs)
        self._callback(result)

    def is_finished(self):
        return self._result == None

    def get_result(self):
        return self._result
