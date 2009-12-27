'''defines objects that make requests to the server on a thread'''

import urllib
import httplib
import threading

from uuid import uuid4

import XmlParser
import XmlManager
import msgs
import e3

import common
import challenge

from debugger import dbg
from Command import Command

def safe_split(text, start, stop, default=""):
    '''try to get the content on text between start and stop,
    if fauls return default
    '''
    try:
        return text.split(start)[1].split(stop)[0]
    except IndexError:
        return default

def build_role(account, role, key, add=True):
    '''build a request to add account to the role if add is True, if False
    build the request to remove account from the role'''
    if add:
        action = 'http://www.msn.com/webservices/AddressBook/AddMember'
        body = XmlManager.get('addmember', key, role, account)
    else:
        action = 'http://www.msn.com/webservices/AddressBook/DeleteMember'
        body = XmlManager.get('deletemember', key, role, account)

    return Request(action, 'omega.contacts.msn.com', 443,
        '/abservice/SharingService.asmx', body)

def get_key(session, host='contacts.msn.com', escape=True):
    '''return the key to call the web services from the session'''
    key = session.extras[host]['security']

    if escape:
        return key.replace('&', '&amp;')

    return key

class Request(object):
    '''a class that represents a request'''

    def __init__(self, action, host, port, path, body):
        '''constructor'''
        self.action = action
        self.host = host
        self.port = port
        self.path = path
        self.body = body

class Response(object):
    '''a class that represents a response'''

    def __init__(self, body, status, reason):
        '''class constructor'''
        self.body = body
        self.status = status
        self.reason = reason

    def __str__(self):
        return "%s - %s\n%s" % (self.status, self.reason, self.body)

class BaseRequester(threading.Thread):
    '''the base class to build requester threads'''

    def __init__(self, session):
        '''class constructor'''
        threading.Thread.__init__(self)
        self.session = session

    def make_request(self, request):
        '''send the soap request to the server'''
        headers = {
            'SOAPAction': request.action,
            'Content-Type': 'text/xml; charset=utf-8',
            'Cookie': 'MSPAuth=' + self.session.extras['MSPAuth'][:-2] + \
              ';MSPProf=' + self.session.extras['MSPProf'],
            'Host': request.host,
            'Content-Length': str(len(request.body)),
            'User-Agent': 'MSN Explorer/9.0 (MSN 8.0; TmstmpExt)',
            'Connection': 'Keep-Alive',
            'Cache-Control': 'no-cache',
        }

        conn = None

        if request.port == 443:
            conn = httplib.HTTPSConnection(request.host, request.port)
        else:
            conn = httplib.HTTPConnection(request.host, request.port)

        conn.request('POST', request.path, request.body, headers)
        conn_response = conn.getresponse()

        response = Response(conn_response.read(), conn_response.status,
            conn_response.reason)

        return response

class Requester(BaseRequester):
    '''a class that makes a soap request on a thread'''

    def __init__(self, session, action, host, port, path, body):
        '''class constructor, session is the session object'''
        BaseRequester.__init__(self, session)

        self.session = session
        self.request = Request(action, host, port, path, body)

    def run(self):
        '''main method of the thread, make the request and handle the response
        '''
        dbg('running request ' + self.request.action, 'req', 1)
        response = self.make_request(self.request)
        self.handle_response(self.request, response)
        dbg('request finished', 'req', 1)

    def handle_response(self, request, response):
        '''override this to do something with the response'''
        pass

class TwoStageRequester(BaseRequester):
    '''a class that does two request sequentially, if the first request fails
    then the second request doesn't run, if the second request fails
    a fallback is ran'''

    def __init__(self, session, command_queue, first_req, second_req,
        fallback_req=None):
        '''class constructor'''
        BaseRequester.__init__(self, session)

        self.command_queue = command_queue
        self.first_req = first_req
        self.second_req = second_req
        self.fallback_req = fallback_req

    def run(self):
        '''the main method on the class'''
        dbg('running first request ' + self.first_req.action, 'req', 1)
        response = self.make_request(self.first_req)
        if response.status != 200:
            dbg('first request ' + self.first_req.action + ' failed, cleanning up', 'req', 1)
            self._on_first_failed(response)
            dbg(response.body, 'req', 4)
            return
        else:
            self._on_first_succeed(response)

        dbg('running second request ' + self.second_req.action, 'req', 1)
        response = self.make_request(self.second_req)
        if response.status != 200:
            dbg('second request ' + self.second_req.action + ' failed, cleanning up', 'req', 1)
            dbg(response.body, 'req', 4)
            self._on_second_failed(response)
            if self.fallback_req is not None:
                dbg('running fallback request ' + self.fallback_req.action, 'req', 1)
                self.make_request(self.fallback_req)
        else:
            self._on_second_succeed(response)

        dbg('request finished', 'req', 1)

    def _on_first_succeed(self, response):
        '''handle the first request if succeeded'''
        pass

    def _on_first_failed(self, response):
        '''handle the first request if failed'''
        pass

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        pass

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        pass

class Membership(Requester):
    '''make the request to get the membership list'''
    def __init__(self, session, command_queue, on_login, started_from_cache):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to be
        sent, if on_login is true, then some commands need to be
        sent in order to inform the server about our contacts'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/FindMembership',
          'contacts.msn.com', 443, '/abservice/SharingService.asmx',
          XmlManager.get('membership', get_key(session)))

        self.command_queue = command_queue
        self.on_login = on_login
        self.started_from_cache = started_from_cache

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            parser = XmlParser.MembershipParser(response.body)
            self.session.contacts.pending = {}
            self.session.contacts.reverse = {}
            pending = self.session.contacts.pending
            reverse = self.session.contacts.reverse
            contacts = self.session.contacts.contacts
            new_accounts = []

            for membership in parser.memberships:
                role = membership['MemberRole']

                for member in membership['Members']:
                    if 'PassportName' in member:
                        email = member['PassportName'].lower()
                    else:
                        continue

                    if email in contacts:
                        contact = contacts[email]
                    else:
                        contact = e3.Contact(email)

                    if role == 'Pending':
                        pending[email] = contact
                        contact.attrs['pending'] = True

                        if 'DisplayName' in member:
                            contact.nick = member['DisplayName']

                    if role == 'Reverse':
                        reverse[email] = contact
                        contact.attrs['Reverse'] = True

                    if role == 'Allow':
                        new_accounts.append(email)
                        contacts[email] = contact

                    if role == 'Block':
                        contact.blocked = True
                    else:
                        contact.blocked = False

                    if 'CID' in member:
                        contact.attrs['CID'] = member['CID']

                all_accounts = set(contacts.keys())
                removed_accounts = all_accounts.difference(new_accounts)

                for email in removed_accounts:
                    # TODO: send some kind of signal to inform to remove the
                    # contact
                    del contacts[email]

            DynamicItems(self.session, self.command_queue,
                self.on_login, self.started_from_cache).start()
        else:
            dbg('error requesting membership ' + response.status, 'req', 1)
            dbg(response.body, 'req', 4)


class DynamicItems(Requester):
    '''make the request to get the dynamic items'''
    def __init__(self, session, command_queue, on_login, started_from_cache):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to be
        sent, if on_login is true, then some commands need to be
        sent in order to inform the server about our contacts'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABFindAll',
          'contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('dynamicitems', get_key(session)))

        self.command_queue = command_queue
        self.on_login = on_login
        self.started_from_cache = started_from_cache

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            parser = XmlParser.DynamicParser(response.body)
            # Retrieve groups
            for group_dict in parser.groups:
                group_id = group_dict['groupId']
                group_name = group_dict['name']

                if group_id in self.session.groups:
                    self.session.groups[group_id].name = group_name
                else:
                    self.session.groups[group_id] = \
                        e3.Group(group_name, group_id)

            # Retrieve contacts
            for contact_dict in parser.contacts:
                if 'isMessengerUser' in contact_dict \
                  and 'passportName' in contact_dict \
                  and contact_dict['isMessengerUser'] == 'true':
                    # valid
                    email = contact_dict['passportName'].lower()
                    if email in self.session.contacts.contacts:
                        contact = self.session.contacts.contacts[email]
                    else:
                        contact = e3.Contact(email)
                        self.session.contacts.contacts[email] = contact
                else:
                    continue

                contact.identifier = contact_dict.get('contactId', '')
                contact.attrs['CID'] = contact_dict.get('CID', '')

                contact.groups = []
                for guid in contact_dict['groupIds']:
                    contact.groups.append(guid)
                    group = self.session.groups[guid]

                    if contact.account not in group.contacts:
                        group.contacts.append(contact.account)

                for ann in contact_dict['Annotations']:
                    if ann.get('Name', None) == 'AB.NickName':
                        contact.alias = urllib.unquote(ann['Value'])
                        break

                if not contact.nick:
                    contact.nick = urllib.unquote(contact_dict.get(
                        'displayName', contact.account))

                contact.attrs['mobile'] = \
                    contact_dict.get('isMobileIMEnabled', None) == 'true'

                contact.attrs['space'] = \
                    contact_dict.get('hasSpace', None) == 'true'

            dbg('dynamic finished', 'req', 1)

            self.session.contacts.me.identifier = \
                response.body.split('<contactType>Me</contactType>')\
                [1].split('</CID>')[0].split('<CID>')[1].strip()

            # get our nick
            try:
                nick = response.body.split('<contactType>Me</contactType>')\
                    [1].split('</displayName>')[0].split('<displayName>')[1]
                nick = common.unescape(nick)
            except IndexError:
                nick = self.session.contacts.me.account

            if not self.session.contacts.me.nick or \
                self.session.contacts.me != self.session.account.account:
                self.session.contacts.me.nick = nick

            if self.on_login:
                # set our nick
                self.command_queue.put(Command('PRP', params=('MFN',
                    urllib.quote(nick))))
                self.session.add_event(e3.Event.EVENT_NICK_CHANGE_SUCCEED, nick)

                if not self.started_from_cache:
                    self.command_queue.put(Command('BLP', params=('BL',)))

            accounts = self.session.contacts.pending.keys()
            for account in accounts:
                # account in pending that is already on some other role
                # (corrupted userlist)
                if account in self.session.contacts.contacts or account in self.session.contacts.reverse:
                    del self.session.contacts.pending[account]
                    # this line doen't work for accounts on corrupted userlists
                    # RemovePendingContact(self.session, account).start()

            self.session.add_event(e3.Event.EVENT_CONTACT_LIST_READY)
            self.session.logger.add_contact_by_group(
                self.session.contacts.contacts, self.session.groups)

            if not self.started_from_cache:
                for adl in self.session.contacts.get_adls():
                    self.command_queue.put(Command('ADL', payload=adl))

            GetProfile(self.session, self.session.contacts.me.identifier).start()

        else:
            dbg('error requestion dynamic items', 'req', 1)

class AddContact(Requester):
    '''make the request to add a contact to the contact list'''
    def __init__(self, session, account, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABContactAdd',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('addcontact', get_key(session), account))

        self.account = account
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.command_queue.put(Command('ADL',
                payload=common.build_adl(self.account, 1)))
            self.command_queue.put(Command('ADL',
                payload=common.build_adl(self.account, 2)))

            self.session.contacts.contacts[self.account] = e3.Contact(self.account)
            self.session.add_event(e3.Event.EVENT_CONTACT_ADD_SUCCEED,
                self.account)
        else:
            self.session.add_event(e3.Event.EVENT_CONTACT_ADD_FAILED, self.account)

class RemoveContact(Requester):
    '''make the request to remove a contact from the contact list'''
    def __init__(self, session, cid, account, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABContactDelete',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('deletecontact', get_key(session), cid))

        self.cid = cid
        self.account = account
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            if self.account in self.session.contacts.contacts:
                del self.session.contacts.contacts[self.account]

            self.session.add_event(e3.Event.EVENT_CONTACT_REMOVE_SUCCEED,
                self.account)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_CONTACT_REMOVE_FAILED,
                self.account)

class RemovePendingContact(Requester):
    '''make the request to remove a contact from the contact list'''
    def __init__(self, session, account):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/DeleteMember',
          'omega.contacts.msn.com', 443, '/abservice/SharingService.asmx',
          XmlManager.get('deletemember', get_key(session), 'Pending', account))

        self.account = account

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            if self.account in self.session.contacts.pending:
                del self.session.contacts.pending[self.account]
            self.session.add_event(e3.Event.EVENT_CONTACT_REJECT_SUCCEED,
                self.account)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_CONTACT_REJECT_FAILED,
                self.account)

class ChangeNick(Requester):
    '''make the request to change the nick on the server'''
    def __init__(self, session, nick, account, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABContactUpdate',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('changenick', get_key(session), 'Me', nick))

        self.nick = nick
        self.account = account
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.command_queue.put(Command('PRP', params=('MFN',
                urllib.quote(self.nick))))
            self.session.contacts.me.nick = self.nick
            self.session.add_event(e3.Event.EVENT_NICK_CHANGE_SUCCEED,
               self.nick)
            self.session.logger.log('nick change', self.account.status,
                self.nick, self.account)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_NICK_CHANGE_FAILED, self.nick)

class ChangeAlias(Requester):
    '''make the request to change the alias on the server'''
    def __init__(self, session, cid, account, alias, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABContactUpdate',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('renamecontact', get_key(session), cid, alias))

        self.alias = alias
        self.account = account
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.session.contacts.contacts[self.account].alias = self.alias
            self.session.add_event(e3.Event.EVENT_CONTACT_ALIAS_SUCCEED,
                self.account)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_CONTACT_ALIAS_FAILED,
                self.account)

class AddGroup(Requester):
    '''make the request to add a group'''
    def __init__(self, session, name, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABGroupAdd',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('addgroup', get_key(session), name))

        self.name = name
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            gid = common.get_value_between(response.body, '<guid>', '</guid>')
            self.session.groups[gid] = e3.Group(self.name, gid)

            self.session.add_event(e3.Event.EVENT_GROUP_ADD_SUCCEED,
                self.name, gid)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_GROUP_ADD_FAILED, self.name)

class RemoveGroup(Requester):
    '''make the request to remove a group'''
    def __init__(self, session, gid, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABGroupDelete', \
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx', \
          XmlManager.get('deletegroup', get_key(session), gid))

        self.gid = gid
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            if self.gid in self.session.groups:
                del self.session.groups[self.gid]

            self.session.add_event(e3.Event.EVENT_GROUP_REMOVE_SUCCEED, self.gid)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_GROUP_REMOVE_FAILED, self.gid)

class RenameGroup(Requester):
    '''make the request to rename a group'''
    def __init__(self, session, gid, name, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABGroupUpdate', \
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx', \
          XmlManager.get('renamegroup', get_key(session), gid, name))

        self.gid = gid
        self.name = name
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.session.groups[self.gid] = e3.Group(self.name, self.gid)

            self.session.add_event(e3.Event.EVENT_GROUP_RENAME_SUCCEED,
                self.gid, self.name)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_GROUP_RENAME_FAILED,
                self.gid, self.name)

class AddToGroup(Requester):
    '''add a contact to a group'''
    def __init__(self, session, cid, account, gid, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABGroupContactAdd',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('moveusertogroup', get_key(session), gid, cid))

        self.cid = cid
        self.gid = gid
        self.account = account
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.session.contacts.contacts[self.account].groups.append(self.gid)
            self.session.groups[self.gid].contacts.append(self.account)

            self.session.add_event(e3.Event.EVENT_GROUP_ADD_CONTACT_SUCCEED,
                self.gid, self.cid)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_GROUP_ADD_CONTACT_FAILED,
                self.gid, self.cid)

class RemoveFromGroup(Requester):
    '''remove a contact from a group'''
    def __init__(self, session, cid, account, gid, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABGroupContactDelete',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('deleteuserfromgroup', get_key(session), cid, gid))

        self.cid = cid
        self.gid = gid
        self.account = account
        self.command_queue = command_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            if self.account in self.session.groups[self.gid].contacts:
                self.session.groups[self.gid].contacts.remove(self.account)

            if self.gid in self.session.contacts.contacts[self.account].groups:
                self.session.contacts.contacts[self.account].groups\
                    .remove(self.gid)

            self.session.add_event(e3.Event.EVENT_GROUP_REMOVE_CONTACT_SUCCEED,
                self.gid, self.cid)
        else:
            dbg(response.body + '\n' + request.body, 'req', 4)
            self.session.add_event(e3.Event.EVENT_GROUP_REMOVE_CONTACT_FAILED,
                self.gid, self.cid)

class BlockContact(TwoStageRequester):
    '''add a contact to the Block role and remove him from the Allow role'''

    def __init__(self, session, account, command_queue):
        TwoStageRequester.__init__(self, session, command_queue,
            build_role(account, 'Allow', get_key(session), False),
            build_role(account, 'Block', get_key(session), True),
            build_role(account, 'Allow', get_key(session), True))

        self.account = account

    def _on_first_succeed(self, response):
        '''handle the first request if succeeded'''
        self.command_queue.put(Command('RML',
            payload=common.build_adl(self.account, 2)))

    def _on_first_failed(self, response):
        '''handle the first request if failed'''
        self.session.add_event(e3.Event.EVENT_CONTACT_BLOCK_FAILED, self.account)

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        self.command_queue.put(Command('ADL',
            payload=common.build_adl(self.account, 4)))

        self.session.contacts.contacts[self.account].blocked = True

        self.session.add_event(e3.Event.EVENT_CONTACT_BLOCK_SUCCEED, self.account)

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        self.command_queue.put(Command('ADL',
            payload=common.build_adl(self.account, 2)))
        self.session.add_event(e3.Event.EVENT_CONTACT_BLOCK_FAILED, self.account)

class UnblockContact(TwoStageRequester):
    '''add a contact to the Allow role and remove him from the Block role'''

    def __init__(self, session, account, command_queue):
        TwoStageRequester.__init__(self, session, command_queue,
            build_role(account, 'Block', get_key(session), False),
            build_role(account, 'Allow', get_key(session), True),
            build_role(account, 'Block', get_key(session), True))

        self.account = account

    def _on_first_succeed(self, response):
        '''handle the first request if succeeded'''
        self.command_queue.put(Command('RML',
            payload=common.build_adl(self.account, 4)))

    def _on_first_failed(self, response):
        '''handle the first request if failed'''
        self.session.add_event(e3.Event.EVENT_CONTACT_UNBLOCK_FAILED, self.account)

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        self.command_queue.put(Command('ADL',
            payload=common.build_adl(self.account, 2)))

        self.session.contacts.contacts[self.account].blocked = False

        self.session.add_event(e3.Event.EVENT_CONTACT_UNBLOCK_SUCCEED,
            self.account)

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        self.command_queue.put(Command('ADL',
            payload=common.build_adl(self.account, 4)))
        self.session.add_event(e3.Event.EVENT_CONTACT_UNBLOCK_FAILED, self.account)

class MoveContact(TwoStageRequester):
    '''remove a contact from a group and add it to another'''

    def __init__(self, session, cid, account, src_gid, dest_gid, command_queue):
        TwoStageRequester.__init__(self, session, command_queue,
            Request(\
              'http://www.msn.com/webservices/AddressBook/ABGroupContactAdd',
              'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
              XmlManager.get('moveusertogroup', get_key(session), dest_gid,
                 cid)),
            Request(\
              'http://www.msn.com/webservices/AddressBook/ABGroupContactDelete',
              'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
              XmlManager.get('deleteuserfromgroup', get_key(session), cid,
                src_gid)),
            Request(\
              'http://www.msn.com/webservices/AddressBook/ABGroupContactDelete',
              'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
              XmlManager.get('deleteuserfromgroup', get_key(session), cid,
                dest_gid)))

        self.src_gid = src_gid
        self.dest_gid = dest_gid
        self.cid = cid
        self.account = account

    def _on_first_failed(self, response):
        '''handle the first request if failed'''
        self.session.add_event(e3.Event.EVENT_CONTACT_MOVE_FAILED,
            self.cid, self.src_gid, self.dest_gid)

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        self.session.contacts.contacts[self.account]\
            .groups.append(self.dest_gid)
        self.session.contacts.contacts[self.account]\
            .groups.remove(self.src_gid)
        self.session.groups[self.src_gid].contacts.remove(self.account)
        self.session.groups[self.dest_gid].contacts.append(self.account)

        self.session.add_event(e3.Event.EVENT_CONTACT_MOVE_SUCCEED,
            self.cid, self.src_gid, self.dest_gid)

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        self.session.add_event(e3.Event.EVENT_CONTACT_MOVE_FAILED,
            self.cid, self.src_gid, self.dest_gid)

class SendOIM(Requester):
    '''make the request to send an oim'''
    def __init__(self, session, msg_queue, contact, message,
                  lockkey='', seq=1, first=True):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        me = session.contacts.me
        passport_id = session.extras['messengersecure.live.com']['security']
        nick = '=?%s?%s?=%s?=' % (
                'utf-8','B', me.display_name.encode('base64').strip())

        run_id = str(uuid4())

        content = message.encode('base64').strip()
        send_xml = XmlManager.get('sendoim', me.account, nick, common.MSNP_VER,
                                  common.BUILD_VER, contact, passport_id,
                                  challenge._PRODUCT_ID, str(lockkey),
                                  str(seq), run_id, str(seq), content)
        send_xml = send_xml.replace('\\r\\n', '\r\n')

        Requester.__init__(self, session,
          'http://messenger.live.com/ws/2006/09/oim/Store2',
          'ows.messenger.msn.com',443,'/OimWS/oim.asmx',
          send_xml.strip())

        self.contact = contact
        self.message = message
        self.oid = ''
        self.seq = seq
        self.first = first
        self.msg_queue = msg_queue

        dbg('FROM:%s TO:%s' % (me.display_name, contact), 'req', 1)

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            #self.msg_queue.add_event(e3.Event.EVENT_OIM_SEND_SUCCEED, self.oid)
            dbg('OIM sent ' + self.contact, 'req', 1)
        else:
            start = '<LockKeyChallenge xmlns="http://messenger.msn.com/'\
                    'ws/2004/09/oim/">'
            end = '</LockKeyChallenge>'
            lockkey_hash = common.get_value_between(response.body, start, end)

            if lockkey_hash:
                lockkey = challenge.do_challenge(str(lockkey_hash))
                SendOIM(self.session, self.msg_queue, self.contact,
                        self.message, lockkey, self.seq+1, False).start()
            else:
                dbg('Can\'t send OIM, fail', 'req', 1)
                dbg(response.body, 'req', 4)
                self.session.add_event(e3.Event.EVENT_ERROR,
                             'to many retries sending oims')
                dbg('to many retries sending oim', 'req', 1)

class RetriveOIM(Requester):
    '''make the request to retrive an oim'''
    def __init__(self, session, oim_data, msg_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to
        send'''
        t, p = session.extras['messenger.msn.com']['security'][2:].split('&p=')
        xml_oim = XmlManager.get('getoim', t, p, oim_data['id'])
        Requester.__init__(self, session,
          'http://www.hotmail.msn.com/ws/2004/09/oim/rsi/GetMessage',
          'rsi.hotmail.com', 443 ,'/rsi/rsi.asmx',
          xml_oim
          )
        self.msg_queue = msg_queue
        self.oim_data = oim_data

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
           oim = msgs.OimParser(response.body)

           oim.id = self.oim_data['id']

           self.msg_queue.put((msgs.Manager.ACTION_OIM_RECEIVED, oim))
        else:
            self.session.add_event(e3.Event.EVENT_ERROR,
                           'Can\'t get oim', self.oim_data['id'])

class RetriveTooLarge(Requester):
    '''make the request to get oims from a soap request'''
    def __init__(self, session, msg_queue):
        '''Return the mail data using soap if there are too many OIMs'''
        t, p = session.extras['messenger.msn.com']['security'][2:].split('&p=')
        xml_oim = XmlManager.get('getmaildata', t, p)
        Requester.__init__(self, session,
          'http://www.hotmail.msn.com/ws/2004/09/oim/rsi/GetMetadata',
          'rsi.hotmail.com', 443 ,'/rsi/rsi.asmx',
          xml_oim
          )
        self.msg_queue = msg_queue

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.msg_queue.put((msgs.Manager.ACTION_MAIL_DATA, response.body))
        else:
            self.session.add_event(e3.Event.EVENT_ERROR, 'Can\'t retrive oims')

class DeleteOIM(Requester):
    '''make the request to delete an oim'''
    def __init__(self, session, oid, msg_queue):
        '''Delete a viewed oim'''
        t, p = session.extras['messenger.msn.com']['security'][2:].split('&p=')
        xml_del_oim = XmlManager.get('deleteoim', t, p, oid)
        Requester.__init__(self, session,
          'http://www.hotmail.msn.com/ws/2004/09/oim/rsi/DeleteMessages',
          'rsi.hotmail.com', 443 ,'/rsi/rsi.asmx',
          xml_del_oim
          )
        self.msg_queue = msg_queue
        self.id = oid

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status != 200:
            self.session.add_event(e3.Event.EVENT_ERROR,
                             'Can\'t delete oim %s' % self.id)

class GetProfile(Requester):
    '''make a request to get the nick and personal message'''
    def __init__(self, session, cid):
        '''constructor'''
        key = get_key(session, 'storage.msn.com', False)
        Requester.__init__(self, session,
            'http://www.msn.com/webservices/storage/w10/GetProfile',
            'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
            XmlManager.get('getprofile', key, cid))

        self.session = session
        self.cid = cid

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            nick = safe_split(response.body, '<DisplayName>', '</DisplayName>')
            message = safe_split(response.body, '<PersonalStatus>', '</PersonalStatus>')
            cache_key = safe_split(response.body, '<CacheKey>', '</CacheKey>')
            rid = safe_split(response.body, '<ResourceID>', '</ResourceID>')

            self.session.extras["CacheKey"] = cache_key
            self.session.extras["ResourceID"] = rid

            self.session.contacts.me.nick = nick
            self.session.contacts.me.message = message

            self.session.add_event(e3.Event.EVENT_PROFILE_GET_SUCCEED,
                nick, message)
        else:
            self.session.add_event(e3.Event.EVENT_PROFILE_GET_FAILED,
                 'Can\'t get profile for %s' % self.cid)

class SetProfile(Requester):
    '''make a request to set the nick and personal message'''
    def __init__(self, session, nick, message):
        '''constructor'''
        key = get_key(session, 'storage.msn.com', False)
        cache_key = session.extras["CacheKey"]
        rid = session.extras["ResourceID"]
        self.nick = nick
        self.message = message
        Requester.__init__(self, session,
            'http://www.msn.com/webservices/storage/w10/UpdateProfile',
            'storage.msn.com', 443, '/storageservice/SchematizedStore.asmx',
            XmlManager.get('updateprofile', cache_key, key, rid, nick, message))

        self.session = session

    def handle_response(self, request, response):
        '''handle the response'''
        if response.status == 200:
            self.session.add_event(e3.Event.EVENT_PROFILE_SET_SUCCEED,
                    self.nick, self.message)
        else:
            self.session.add_event(e3.Event.EVENT_PROFILE_SET_FAILED,
                 'Can\'t set profile')

