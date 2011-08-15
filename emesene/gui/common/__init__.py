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

import extension

def import_and_register(category_name, cls):
    try:
        imported_cls = __import__('gui.common.'+cls)
        if extension.get_category(category_name) is None:
            extension.category_register(category_name, eval(cls+'.'+cls))
        else:
            extension.register(category_name, eval(cls+'.'+cls))
        return imported_cls
    except ImportError:
        return None

import_and_register('tray icon', 'MessagingMenu')
import_and_register('tray icon', 'Indicator')
import_and_register('tray icon', 'TrayIcon')
import_and_register('tray icon', 'NoTrayIcon')
import_and_register(('notificationGUI'), 'PyNotification')
import_and_register(('notificationGUI'), 'GtkNotification')
import_and_register(('notificationGUI'), 'GrowlNotification')
import_and_register(('notificationImage'), 'ThemeNotificationImage')
import_and_register(('notificationImage'), 'DummyNotificationImage')
