# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Johann Prieur <johann.prieur@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

import contactcardservice
import scenario

from papyon.service.SOAPUtils import *

import papyon.util.element_tree as ElementTree
import papyon.util.string_io as StringIO
import gobject

import logging

__all__ = ['Spaces']

class Spaces(gobject.GObject):

    __gsignals__ = {
            "contact-card-retrieved" : (gobject.SIGNAL_RUN_FIRST,
                                        gobject.TYPE_NONE,
                                        (object, object))
            }

    def __init__(self, sso, proxies=None):
        gobject.GObject.__init__(self)

        self._ccard = contactcardservice.ContactCardService(sso, proxies)

    # Public API
    def get_contact_card(self, contact):
        ccs = scenario.GetContactCardScenario(self._ccard, contact,
                                              (self.__get_contact_card_cb, contact),
                                              (self.__common_errback,))
        ccs()
    # End of public API

    # Callbacks
    def __get_contact_card_cb(self, ccard, contact):
        print "Contact card retrieved : \n%s\n"  % str(ccard)
        self.emit('contact-card-retrieved', contact, ccard)

    def __common_errback(self, error_code, *args):
        print "The fetching of the contact card returned an error (%s)" % error_code


gobject.type_register(Spaces)

if __name__ == '__main__':
    import sys
    import getpass
    import signal
    import gobject
    import logging
    from papyon.service.SingleSignOn import *
    from papyon.service.AddressBook import *

    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        account = raw_input('Account: ')
    else:
        account = sys.argv[1]

    if len(sys.argv) < 3:
        password = getpass.getpass('Password: ')
    else:
        password = sys.argv[2]

    mainloop = gobject.MainLoop(is_running=True)
    
    signal.signal(signal.SIGTERM,
            lambda *args: gobject.idle_add(mainloop.quit()))

    def address_book_state_changed(address_book, pspec, sso):
        if address_book.state == AddressBookState.SYNCHRONIZED:
            pass

    sso = SingleSignOn(account, password)

    address_book = AddressBook(sso)
    address_book.connect("notify::state", address_book_state_changed, sso)
    address_book.sync()

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
