#!/usr/bin/env python
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

import subprocess

class Contributor(object):
    def __init__(self, name, mail):
        self.name = name
        self.mail = mail
        self.commits = 1

    def __str__(self):
        return "%s %s %s" % (self.name, self.mail, self.commits)

CONTRIB_NAMES = {}
CONTRIB_MAILS = {}
CONTRIBS = []
CONTRIB_STRING = ''
split_char = "*"

p = subprocess.Popen(["git log --all --format='%aN" + split_char + "<%aE>'"], 
                     stdout = subprocess.PIPE, shell = True)
out = p.communicate()[0]
#print out
lines = out.split("\n")
for line in lines:
    try:
        name, mail = line.split(split_char)
        if name in CONTRIB_NAMES:
            CONTRIB_NAMES[name].commits += 1
            continue
        if mail in CONTRIB_MAILS:
            CONTRIB_MAILS[mail].commits += 1
            continue
        c = Contributor(name, mail)
        CONTRIB_NAMES[name] = c
        CONTRIB_MAILS[mail] = c
        CONTRIBS.append(c)
    except ValueError:
        pass

c_sorted = sorted(CONTRIBS, key=lambda contributor: contributor.commits, reverse=True)
for c_sort in c_sorted:
    CONTRIB_STRING += '%s %s\n' % (c_sort.name, c_sort.mail)
    #print c_sort

f = open("CONTRIBUTORS", "w")
f.write(CONTRIB_STRING)
f.close()
