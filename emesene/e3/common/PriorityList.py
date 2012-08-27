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

class PriorityList:
    ''' this class implements a list of items ordered by their priority.
    '''
    def __init__(self):
        self.items = []

    def append(self, i, prio=-99):
        ''' append a tuple (priority, item) 
            priority goes from -99 (lower) to 0 (higher)
        '''
        self.items.append((prio, i))
        self.items.sort(key=lambda i: i[0], reverse=True)

    def remove(self, i):
        ''' remove a tuple given an item '''
        for item in self.items:
            if item[1] == i:
                self.items.remove(item)

    def sorted(self):
        ''' returns a sorted copy of items '''
        return [k[1] for k in self.items]

def main():
    p = PriorityList()
    p.append(1)
    p.append(2)
    p.append(3)
    p.append(4)
    p.append(4, -20)
    p.append(5)
    p.append(5, 0)

    print p.items
    print p.sorted()
    print "========================="

    for item in p.sorted():
        print item

    print "========================="

    p.remove(5)
    p.remove(1)

    print p.items
    print p.sorted()

if __name__ == "__main__":
    main()
