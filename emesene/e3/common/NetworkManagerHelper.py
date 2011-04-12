#  
#  Copyright (c) 2010 Mohamed Amine IL Idrissi
#  Copyright (c) 2011 Canonical
#  
#  Author:  Alex Chiang <achiang@canonical.com>
#           Michael Vogt <michael.vogt@ubuntu.com>
#  Author: Mohamed Amine IL Idrissi <ilidrissiamine@gmail.com>
#
#  modified for emesene by Riccardo (c10ud) <c10ud.dev@gmail.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

from e3.base.Event import Event
import sys
import gobject
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import logging
log = logging.getLogger("emesene.e3.common.NetworkManagerHelper")
import extension

class AlertWatcher(gobject.GObject):
    """ a class that checks for alerts and reports them, like a battery
    or network warning """
    
    __gsignals__ = {"network-alert": (gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_INT,)),
                    "battery-alert": (gobject.SIGNAL_RUN_FIRST,
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_BOOLEAN,)),
                    "network-3g-alert": (gobject.SIGNAL_RUN_FIRST,
                                         gobject.TYPE_NONE,
                                        (gobject.TYPE_BOOLEAN,
                                         gobject.TYPE_BOOLEAN,)),
                    }
    
    def __init__(self):
        gobject.GObject.__init__(self)
        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
        self.network_state = 3 # make it always connected if NM isn't available
        
    def check_alert_state(self):
        try:
            obj = self.bus.get_object("org.freedesktop.NetworkManager",
                                      "/org/freedesktop/NetworkManager")
            obj.connect_to_signal("StateChanged",
                                  self._on_network_state_changed,
                                  dbus_interface="org.freedesktop.NetworkManager")
            interface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
            self.network_state = interface.Get("org.freedesktop.NetworkManager", "State")
            self._network_alert(self.network_state)
            # emesene: disable stuff we don't need
            # power
            #obj = self.bus.get_object('org.freedesktop.UPower',
            #                          '/org/freedesktop/UPower')
            #obj.connect_to_signal("Changed", self._power_changed,
            #                      dbus_interface="org.freedesktop.UPower")
            #self._power_changed()
            # 3g
            #self._update_3g_state()
        except dbus.exceptions.DBusException, e:
            pass

    def _on_network_state_changed(self, state):
        self._network_alert(state)
        self._update_3g_state()

    def _update_3g_state(self):
        nm = NetworkManagerHelper()
        on_3g = nm.is_active_connection_gsm_or_cdma()
        is_roaming = nm.is_active_connection_gsm_or_cdma_roaming()
        self._network_3g_alert(on_3g, is_roaming)

    def _network_3g_alert(self, on_3g, is_roaming):
        self.emit("network-3g-alert", on_3g, is_roaming)
    
    def _network_alert(self, state):
        self.network_state = state
        self.emit("network-alert", state)
        
    def _power_changed(self):
        obj = self.bus.get_object("org.freedesktop.UPower", \
                                "/org/freedesktop/UPower")
        interface = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        on_battery = interface.Get("org.freedesktop.UPower", "OnBattery")
        self.emit("battery-alert", on_battery)

class DBusNetworkChecker():
    ''' this class does lazy checks for network availability and 
    disconnects emesene if the network goes down '''
    def __init__(self):
        self.__session = None
        self.connected = True

    #Public methods
    def set_new_session(self, session):
        self.__session = session

        self.alert_watcher = AlertWatcher ()
        self.alert_watcher.connect("network-alert", self._on_network_alert)
        self.alert_watcher.check_alert_state()

    def stop(self):
        pass

    #Callback functions
    def _on_network_alert(self, watcher, state):
        # do not set the buttons to sensitive/insensitive until NM
        # can deal with dialup connections properly
        if state == NetworkManagerHelper.NM_STATE_CONNECTING:
            self.connected = False
        # in doubt (STATE_UNKNOWN), assume connected
        elif state in (NetworkManagerHelper.NM_STATE_CONNECTED,
                       NetworkManagerHelper.NM_STATE_UNKNOWN):
            self.connected = True
        else:
            self.connected = False

        if not self.connected:
            # 1 means reconnect
            self.__session.add_event(Event.EVENT_DISCONNECTED, 'Network error', 1)

extension.register('external api', DBusNetworkChecker)


class ModemManagerHelper(object):

    # data taken from 
    #  http://projects.gnome.org/NetworkManager/developers/mm-spec-04.html
    MM_DBUS_IFACE = "org.freedesktop.ModemManager"
    MM_DBUS_IFACE_MODEM = MM_DBUS_IFACE + ".Modem"

    # MM_MODEM_TYPE
    MM_MODEM_TYPE_GSM = 1
    MM_MODEM_TYPE_CDMA = 2

    # GSM
    # Not registered, not searching for new operator to register. 
    MM_MODEM_GSM_NETWORK_REG_STATUS_IDLE = 0
    # Registered on home network. 
    MM_MODEM_GSM_NETWORK_REG_STATUS_HOME = 1
    # Not registered, searching for new operator to register with. 
    MM_MODEM_GSM_NETWORK_REG_STATUS_SEARCHING = 2
    # Registration denied. 
    MM_MODEM_GSM_NETWORK_REG_STATUS_DENIED = 3
    # Unknown registration status. 
    MM_MODEM_GSM_NETWORK_REG_STATUS_UNKNOWN = 4
    # Registered on a roaming network. 
    MM_MODEM_GSM_NETWORK_REG_STATUS_ROAMING = 5

    # CDMA
    # Registration status is unknown or the device is not registered.
    MM_MODEM_CDMA_REGISTRATION_STATE_UNKNOWN = 0
    # Registered, but roaming status is unknown or cannot be provided 
    # by the device. The device may or may not be roaming.
    MM_MODEM_CDMA_REGISTRATION_STATE_REGISTERED = 1
    #     Currently registered on the home network.
    MM_MODEM_CDMA_REGISTRATION_STATE_HOME = 2
    #     Currently registered on a roaming network.
    MM_MODEM_CDMA_REGISTRATION_STATE_ROAMING = 3

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object("org.freedesktop.ModemManager", 
                                         "/org/freedesktop/ModemManager")
        modem_manager = dbus.Interface(self.proxy, self.MM_DBUS_IFACE)
        self.modems = modem_manager.EnumerateDevices()

    @staticmethod
    def get_dbus_property(proxy, interface, property):
        props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        property = props.Get(interface, property)
        return property

    def is_gsm_roaming(self):
        for m in self.modems:
            dev = self.bus.get_object(self.MM_DBUS_IFACE, m)
            type = self.get_dbus_property(dev, self.MM_DBUS_IFACE_MODEM, "Type")
            if type != self.MM_MODEM_TYPE_GSM:
                continue
            net = dbus.Interface(dev, self.MM_DBUS_IFACE_MODEM + ".Gsm.Network")
            reg = net.GetRegistrationInfo()
            # Be conservative about roaming. If registration unknown, 
            # assume yes.
            # MM_MODEM_GSM_NETWORK_REG_STATUS
            if reg[0] in (self.MM_MODEM_GSM_NETWORK_REG_STATUS_UNKNOWN,
                          self.MM_MODEM_GSM_NETWORK_REG_STATUS_ROAMING):
                return True
        return False

    def is_cdma_roaming(self):
        for m in self.modems:
            dev = self.bus.get_object(self.MM_DBUS_IFACE, m)
            type = self.get_dbus_property(dev, self.MM_DBUS_IFACE_MODEM, "Type")
            if type != self.MM_MODEM_TYPE_CDMA:
                continue
            cdma = dbus.Interface(dev, self.MM_DBUS_IFACE_MODEM + ".Cdma")
            (cmda_1x, evdo) = cdma.GetRegistrationState()
            # Be conservative about roaming. If registration unknown, 
            # assume yes.
            # MM_MODEM_CDMA_REGISTRATION_STATE
            roaming_states = (self.MM_MODEM_CDMA_REGISTRATION_STATE_REGISTERED,
                              self.MM_MODEM_CDMA_REGISTRATION_STATE_ROAMING)
            # evdo trumps cmda_1x (thanks to Mathieu Trudel-Lapierre)
            if evdo in roaming_states:
                return True
            elif cmda_1x in roaming_states:
                return True
        return False

class NetworkManagerHelper(object):
    NM_DBUS_IFACE = "org.freedesktop.NetworkManager"

    # connection states
    NM_STATE_UNKNOWN = 0
    NM_STATE_ASLEEP = 1
    NM_STATE_CONNECTING = 2
    NM_STATE_CONNECTED = 3
    NM_STATE_DISCONNECTED = 4

    # The device type is unknown. 
    NM_DEVICE_TYPE_UNKNOWN = 0
    # The device is wired Ethernet device. 
    NM_DEVICE_TYPE_ETHERNET = 1
    # The device is an 802.11 WiFi device. 
    NM_DEVICE_TYPE_WIFI = 2
    # The device is a GSM-based cellular WAN device. 
    NM_DEVICE_TYPE_GSM = 3
    # The device is a CDMA/IS-95-based cellular WAN device. 
    NM_DEVICE_TYPE_CDMA = 4

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.proxy = self.bus.get_object("org.freedesktop.NetworkManager", 
                                         "/org/freedesktop/NetworkManager")

    @staticmethod
    def get_dbus_property(proxy, interface, property):
        props = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")
        property = props.Get(interface, property)
        return property

    def is_active_connection_gsm_or_cdma(self):
        res = False
        actives = self.get_dbus_property(
            self.proxy, self.NM_DBUS_IFACE, 'ActiveConnections')
        for a in actives:
            active = self.bus.get_object(self.NM_DBUS_IFACE, a)
            default_route = self.get_dbus_property(
                active, self.NM_DBUS_IFACE + ".Connection.Active", 'Default')
            if not default_route:
                continue
            devs = self.get_dbus_property(
                active, self.NM_DBUS_IFACE + ".Connection.Active", 'Devices')
            for d in devs:
                dev = self.bus.get_object(self.NM_DBUS_IFACE, d)
                type = self.get_dbus_property(
                    dev, self.NM_DBUS_IFACE + ".Device", 'DeviceType')
                if type == self.NM_DEVICE_TYPE_GSM:
                    return True
                elif type == self.NM_DEVICE_TYPE_CDMA:
                    return True
                else:
                    continue
        return res

    def is_active_connection_gsm_or_cdma_roaming(self):
        res = False
        if self.is_active_connection_gsm_or_cdma():
            mmhelper = ModemManagerHelper()
            res |= mmhelper.is_gsm_roaming()
            res |= mmhelper.is_cdma_roaming()
        return res

if __name__ == "__main__":
    
    # test code
    if sys.argv[1:] and sys.argv[1] == "--test":
        mmhelper = ModemManagerHelper()
        print "is_gsm_roaming", mmhelper.is_gsm_roaming()
        print "is_cdma_romaing", mmhelper.is_cdma_roaming()

    # roaming?
    nmhelper = NetworkManagerHelper()
    is_roaming = nmhelper.is_active_connection_gsm_or_cdma_roaming()
    print "roam: ", is_roaming
    if is_roaming:
        sys.exit(1)
    sys.exit(0)
