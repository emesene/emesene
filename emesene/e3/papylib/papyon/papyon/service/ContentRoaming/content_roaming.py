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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import storage
import scenario

from papyon.service.ContentRoaming.constants import *
from papyon.service.ContentRoaming.scenario import *
from papyon.util.async import *

import gobject
import imghdr
import logging

logger = logging.getLogger("papyon.service.content_roaming")

__all__ = ['ContentRoaming', 'ContentRoamingState', 'ContentRoamingError']

class ContentRoaming(gobject.GObject):

    __gsignals__ = {
        "error" : (gobject.SIGNAL_RUN_FIRST,
            gobject.TYPE_NONE,
            (object,)),
        }


    __gproperties__ = {
        "state"            : (gobject.TYPE_INT,
                              "State",
                              "The state of the addressbook.",
                              0, 2, ContentRoamingState.NOT_SYNCHRONIZED,
                              gobject.PARAM_READABLE),
        
        "display-name"     : (gobject.TYPE_STRING,
                              "Display name",
                              "The user's display name on storage",
                              "",
                              gobject.PARAM_READABLE),
        
        "personal-message" : (gobject.TYPE_STRING,
                              "Personal message",
                              "The user's personal message on storage",
                              "",
                              gobject.PARAM_READABLE),

        "display-picture"  : (gobject.TYPE_PYOBJECT,
                              "Display picture",
                              "The user's display picture on storage",
                              gobject.PARAM_READABLE)
        }

    def __init__(self, sso, ab, proxies=None):
        """The content roaming object"""
        gobject.GObject.__init__(self)

        self._storage = storage.Storage(sso, proxies)
        self._ab = ab

        self.__state = ContentRoamingState.NOT_SYNCHRONIZED

        self.__display_name = ''
        self.__personal_message = ''
        self.__display_picture = None

        self._profile_id = None
        self._expression_profile_id = None
        self._display_picture_id = None

    # Properties
    def __get_state(self):
        return self.__state
    def __set_state(self, state):
        self.__state = state
        self.notify("state")
    state = property(__get_state)
    _state = property(__get_state, __set_state)
        
    @property
    def display_name(self):
        return self.__display_name

    @property
    def personal_message(self):
        return self.__personal_message

    @property
    def display_picture(self):
        return self.__display_picture

    ### Public API -----------------------------------------------------------

    def sync(self):
        if self._state != ContentRoamingState.NOT_SYNCHRONIZED:
            return
        self._state = ContentRoamingState.SYNCHRONIZING

        logger.info("Synchronizing")
        gp = GetStoredProfileScenario(self._storage,
                                      (self.__get_dn_and_pm_cb,),
                                      (self.__get_display_picture_cb,),
                                      (self.__common_errback,))
        gp.cid = self._ab.profile.cid
        gp()

    def store(self, display_name=None, personal_message=None,
              display_picture=None, callback=None, errback=None):
        if display_name is None:
            display_name = self.__display_name
        if personal_message is None:
            personal_message = self.__personal_message

        picture_type = None
        if display_picture is not None:
            picture_type = imghdr.what('', display_picture)
            if picture_type is None:
                picture_type = 'png'
            display_picture = ('image/%s' % picture_type, display_picture)

        def store_profile_cb():
            self.__display_name = display_name
            self.__personal_message = personal_message
            self.__display_picture = display_picture
            run(callback)

        logger.info("Store profile (dn='%s', pm='%s', dp='%s')" %
                (display_name, personal_message, picture_type))
        up = StoreProfileScenario(self._storage,
                                  (store_profile_cb,),
                                  (self.__common_errback, errback),
                                  self._ab.profile.cid,
                                  self._profile_id,
                                  self._expression_profile_id,
                                  self._display_picture_id)

        up.display_name = display_name
        up.personal_message = personal_message
        up.display_picture = display_picture

        up()

    ### End of public API ----------------------------------------------------

    # Callbacks
    def __get_dn_and_pm_cb(self, profile_id, expression_profile_id, 
                           display_name, personal_message, display_picture_id):
        logger.info("Retrieved store profile")
        self._profile_id = profile_id
        self._expression_profile_id = expression_profile_id
        self._display_picture_id = display_picture_id

        self.__display_name = display_name
        self.notify("display-name")

        self.__personal_message = personal_message
        self.notify("personal-message")

        if self._display_picture_id is None:
            self._state = ContentRoamingState.SYNCHRONIZED

    def __get_display_picture_cb(self, type, data):
        logger.info("Retrieved display picture")
        self.__display_picture = (type, data)
        self.notify("display-picture")

        self._state = ContentRoamingState.SYNCHRONIZED

    def __common_errback(self, error, errback, *args):
        logger.error("Content Roaming service got error: %s" % str(error))
        run(errback, error)
        self.emit("error", error)

gobject.type_register(ContentRoaming)

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

            def content_roaming_state_changed(cr, pspec):
                 if cr.state == ContentRoamingState.SYNCHRONIZED:
                     print "Content roaming service is now synchronized"
                     
#                     print cr.display_picture
#                      type, data = cr.display_picture
#                      path = '/home/jprieur/projects/papyon.rewrite/papyon/service/ContentRoaming/argh.%s' % type.split('/')[1]
#                      f = open(path, 'w')
#                      f.write(data)

#                      path = '/home/jprieur/projects/papyon.rewrite/papyon/service/ContentRoaming/test.jpeg'
#                      f = open(path, 'r')
#                      cr.store("Pouet pouet", "Brainy lala brainy...", f.read())

            cr = ContentRoaming(sso, address_book)
            cr.connect("notify::state", content_roaming_state_changed)
            cr.sync()

    sso = SingleSignOn(account, password)

    address_book = AddressBook(sso)
    address_book.connect("notify::state", address_book_state_changed, sso)
    address_book.sync()

    while mainloop.is_running():
        try:
            mainloop.run()
        except KeyboardInterrupt:
            mainloop.quit()
