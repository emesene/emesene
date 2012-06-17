# -*- coding: utf-8 -*-
#
# Author: Manuel de la Pena<manuel@canonical.com>
#
# Copyright 2011 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Implementation of a Network Manager using ISesNework in Python."""
from e3.base.Event import Event

import logging
log = logging.getLogger("emesene.e3.common.NetworkManagerHelper")
import extension

from threading import Thread
import pythoncom
 
from win32com.server.policy import DesignatedWrapPolicy
from win32com.client import Dispatch
 
## from EventSys.h
PROGID_EventSystem = "EventSystem.EventSystem"
PROGID_EventSubscription = "EventSystem.EventSubscription"
 
# SENS (System Event Notification Service) values for the events,
# this events contain the uuid of the event, the name of the event to be used
# as well as the method name of the method in the ISesNetwork interface that
# will be executed for the event.
# For more ingo look at:
# http://msdn.microsoft.com/en-us/library/aa377384(v=vs.85).aspx
 
SUBSCRIPTION_NETALIVE = ('{cd1dcbd6-a14d-4823-a0d2-8473afde360f}',
                         'emesene Network Alive',
                         'ConnectionMade')
 
SUBSCRIPTION_NETALIVE_NOQOC = ('{a82f0e80-1305-400c-ba56-375ae04264a1}',
                               'emesene Net Alive No Info',
                               'ConnectionMadeNoQOCInfo')
 
SUBSCRIPTION_NETLOST = ('{45233130-b6c3-44fb-a6af-487c47cee611}',
                        'emesene Network Lost',
                        'ConnectionLost')
 
SUBSCRIPTION_REACH = ('{4c6b2afa-3235-4185-8558-57a7a922ac7b}',
                       'emesene Network Reach',
                       'ConnectionMade')
 
SUBSCRIPTION_REACH_NOQOC = ('{db62fa23-4c3e-47a3-aef2-b843016177cf}',
                            'emesene Network Reach No Info',
                            'ConnectionMadeNoQOCInfo')
 
SUBSCRIPTION_REACH_NOQOC2 = ('{d4d8097a-60c6-440d-a6da-918b619ae4b7}',
                             'emesene Network Reach No Info 2',
                             'ConnectionMadeNoQOCInfo')
 
SUBSCRIPTIONS = [SUBSCRIPTION_NETALIVE,
                 SUBSCRIPTION_NETALIVE_NOQOC,
                 SUBSCRIPTION_NETLOST,
                 SUBSCRIPTION_REACH,
                 SUBSCRIPTION_REACH_NOQOC,
                 SUBSCRIPTION_REACH_NOQOC2 ]
 
SENSGUID_EVENTCLASS_NETWORK = '{d5978620-5b9f-11d1-8dd2-00aa004abd5e}'
SENSGUID_PUBLISHER = "{5fee1bd6-5b9b-11d1-8dd2-00aa004abd5e}"
 
# uuid of the implemented com interface
IID_ISesNetwork = '{d597bab1-5b9f-11d1-8dd2-00aa004abd5e}'
 
class NetworkManager(DesignatedWrapPolicy):
    """Implement ISesNetwork to know about the network status."""
 
    _com_interfaces_ = [IID_ISesNetwork]
    _public_methods_ = ['ConnectionMade',
                        'ConnectionMadeNoQOCInfo', 
                        'ConnectionLost']
    _reg_clsid_ = '{41B032DA-86B5-4907-A7F7-958E59333010}' 
    _reg_progid_ = "emesene.NetworkManager"
 
    def __init__(self, connected_cb=None, connected_cb_info=None,
                 disconnected_cb=None):
        self._wrap_(self)
        self.connected_cb = connected_cb
        self.connected_cb_info = connected_cb_info
        self.disconnected_cb = disconnected_cb
 
    def ConnectionMade(self, *args):
        """Tell that the connection is up again."""
        logging.info('Connection was made.')
        if self.connected_cb_info is not None:
            self.connected_cb_info()
 
    def ConnectionMadeNoQOCInfo(self, *args):
        """Tell that the connection is up again."""
        logging.info('Connection was made no info.')
        if self.connected_cb is not None:
            self.connected_cb()
 
    def ConnectionLost(self, *args):
        """Tell the connection was lost."""
        logging.info('Connection was lost.')
        if self.disconnected_cb is not None:
            self.disconnected_cb() 
 
    def register(self):
        """Register to listen to network events."""
        # call the CoInitialize to allow the registration to run in an other
        # thread
        pythoncom.CoInitialize()
        # interface to be used by com
        manager_interface = pythoncom.WrapObject(self)
        event_system = Dispatch(PROGID_EventSystem)
        # register to listent to each of the events to make sure that
        # the code will work on all platforms.
        for current_event in SUBSCRIPTIONS:
            # create an event subscription and add it to the event
            # service
            event_subscription = Dispatch(PROGID_EventSubscription)
            event_subscription.EventClassId = SENSGUID_EVENTCLASS_NETWORK
            event_subscription.PublisherID = SENSGUID_PUBLISHER
            event_subscription.SubscriptionID = current_event[0]
            event_subscription.SubscriptionName = current_event[1]
            event_subscription.MethodName = current_event[2]
            event_subscription.SubscriberInterface = manager_interface
            event_subscription.PerUser = True
            # store the event
            try:
                event_system.Store(PROGID_EventSubscription, 
                                   event_subscription)
            except pythoncom.com_error as e:
                logging.error(
                    'Error registering %s to event %s', e, current_event[1])
 
        pythoncom.PumpMessages()

class Win32NetworkChecker():
    ''' this class does lazy checks for network availability and 
    disconnects emesene if the network goes down '''
    def __init__(self):
        self.__session = None
        self.connected = True
        self.alert_watcher = None

    #Public methods
    def set_new_session(self, session):
        self.__session = session

        if self.alert_watcher is None:
            self.alert_watcher = NetworkManager(self.connected_cb, self.connected_info_cb, self.disconnected_cb)
            p = Thread(target=self.alert_watcher.register)
            p.start()

    def stop(self):
        pass

    def connected_cb(self):
        self.connected = True

    def connected_info_cb(self):
        self.connected = True

    def disconnected_cb(self):
        self.connected = False
        # 1 means reconnect
        self.__session.add_event(Event.EVENT_DISCONNECTED, 'Network error', 1)

extension.category_register('network checker', Win32NetworkChecker)
extension.set_default('network checker', Win32NetworkChecker)

if __name__ == '__main__':
    # Run an expample of the code so that the user can test the code in
    # real life.
    from threading import Thread
    def connected():
        print 'Connected'

    def connected_info():
        print 'Connected'
        
    def disconnected():
        print 'Disconnected'
 
    manager = NetworkManager(connected, connected_info, disconnected)
    p = Thread(target=manager.register)
    p.start()

