# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
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
'''a module that defines the api of objects that display dialogs'''

import gettext

_ = gettext.gettext

def error(message, response_cb=None, title=_("Error!")):
    '''show an error dialog displaying the message, this dialog should
    have only the option to close and the response callback is optional
    since in few cases one want to know when the error dialog was closed,
    but it can happen, so return stock.CLOSE to the callback if its set'''
    pass

def warning(message, response_cb=None, title=_("Warning")):
    '''show a warning dialog displaying the messge, this dialog should
    have only the option to accept, like the error dialog, the response
    callback is optional, but you have to check if it's not None and
    send the response (that can be stock.ACCEPT or stock.CLOSE, if
    the user closed the window with the x)'''
    pass

def information(message, response_cb=None, title=_("Information"),):
    '''show a warning dialog displaying the messge, this dialog should
    have only the option to accept, like the error dialog, the response
    callback is optional, but you have to check if it's not None and
    send the response (that can be stock.ACCEPT or stock.CLOSE, if
    the user closed the window with the x)'''
    pass

def exception(message, response_cb=None, title=_("Exception"),):
    '''show the message of an exception on a dialog, useful to
    connect with sys.excepthook'''
    pass

def yes_no(message, response_cb, title=_("Confirm"), *args):
    '''show a confirm dialog displaying a question and two buttons:
    Yes and No, return the response as stock.YES or stock.NO or
    stock.CLOSE if the user closes the window'''
    pass

def yes_no_cancel(message, response_cb, title=_("Confirm"), *args):
    '''show a confirm dialog displaying a question and three buttons:
    Yes and No and Cancel, return the response as stock.YES, stock.NO,
    stock.CANCEL or stock.CLOSE if the user closes the window'''
    pass

def accept_cancel(message, response_cb, title=_("Confirm"), *args):
    '''show a confirm dialog displaying information and two buttons:
    Accept and Cancel, return stock.ACCEPT, stock.CANCEL or 
    stock.CLOSE'''
    pass

def contact_added_you(accounts, response_cb, title=("User invitation")):
    '''show a dialog displaying information about users
    that added you to their userlists, the accounts parameter is
    a tuple of mails that represent all the users that added you,
    the way you confirm (one or more dialogs) doesn't matter, but
    you should call the response callback only once with a tuple
    like: ((mail1, stock.YES), (mail2, stock.NO), (mail3, stock.CANCEL))
    YES means add him to your userlist, NO means block him, CANCEL
    means remind me later.'''
    pass

def add_contact(groups, group, response_cb, title=_("Add user")):
    '''show a dialog asking for an user address, and (optional)
    the group(s) where the user should be added, and the group selected
    by default (None to select no group) the response callback
    receives the response type (stock.ADD, stock.CANCEL or stock.CLOSE)
    the account and a tuple of group names where the user should be 
    added (give a empty tuple if you don't implement this feature, 
    the controls are made by the callback, you just ask for the email, 
    don't make any control, you are just implementing a GUI! :P'''
    pass

def add_group(response_cb, title=_("Add group")):
    '''show a dialog asking for a group name, the response callback
    receives the response (stock.ADD, stock.CANCEL, stock.CLOSE)
    and the name of the group, the control for a valid group is made
    on the controller, so if the group is empty you just call the
    callback, to make a unified behaviour, and also, to only implement
    GUI logic on your code and not client logic
    cb args: response, group_name'''
    pass

def set_nick(nick, response_cb, title=_("Change nick")):
    '''show a dialog asking for a new nick and displaying the current
    one, the response_cb receives the old nick, the new nick, 
    and the response (stock.ACCEPT, stock.CANCEL or stock.CLOSE)
    cb args: response, old_nick, new_nick'''
    pass

def set_message(message, response_cb, title=_("Change personal message")):
    '''show a dialog asking for a new personal message and displaying 
    the current one, the response_cb receives the old personal message
    , the new personal message and the response 
    (stock.ACCEPT, stock.CANCEL or stock.CLOSE)
    cb args: response, old_pm, new_pm'''
    pass

def set_picture(path_current, response_cb, title=_("Change picture")):
    '''show a dialog asking for the display picture and return the selected
    one, path_current is the path of the current selected picture.
     Return the new path or None if no new picture is selected'''
    pass

def rename_group(name, response_cb, title=_("Rename group")):
    '''show a dialog with the group name and ask to rename it, the
    response callback receives stock.ACCEPT, stock.CANCEL or stock.CLOSE
    the old and the new name.
    cb args: response, old_name, new_name
    '''
    pass

def set_contact_alias(account, alias, response_cb, title=_("Set alias")):
    '''show a dialog showing the current alias and asking for the new
    one, the response callback receives,  the response 
    (stock.ACCEPT, stock.CANCEL, stock.CLEAR <- to remove the alias 
    or stock.CLOSE), the account, the old and the new alias.
    cb args: response, account, old_alias, new_alias'''
    pass

def about_dialog(name, version, copyright, comments, license, website,
    authors, translators, logo_path):
    '''show an about dialog of the application:
    * title: the title of the window
    * name: the name of the appliaction
    * version: version as string
    * copyright: the name of the copyright holder
    * comments: a description of the application
    * license: the license text
    * website: the website url
    * authors: a list or tuple of strings containing the contributors
    * translators: a string containing the translators
    '''
    pass

def contact_information_dialog(session, account):
    '''shows information about the account'''
    pass
