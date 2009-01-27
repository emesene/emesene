'''defines objects that make requests to the server on a thread'''

import urllib
import httplib
import threading

import XmlParser
import XmlManager
import protocol.Group as Group
import protocol.Contact as Contact
from protocol.Event import Event

from Command import Command
import common

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

def get_key(session):
    '''return the key to call the web services from the session'''
    return session.extras['contacts.msn.com']['security'].replace('&', '&amp;')

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
        
        #print headers
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
        print 'running request', self.request.action
        response = self.make_request(self.request)
        self.handle_response(self.request, response)
        print 'request finished'

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
        print 'running first request', self.first_req.action
        response = self.make_request(self.first_req)
        if response.status != 200:
            print 'first request', self.first_req.action, 'failed, cleanning up'
            self._on_first_failed(response)
            print response.body
            return
        else:
            self._on_first_succeed(response)

        print 'running second request', self.second_req.action
        response = self.make_request(self.second_req)
        if response.status != 200:
            print 'second request', self.second_req.action, \
                'failed, cleanning up'
            print response.body
            self._on_second_failed(response)
            if self.fallback_req is not None:
                print 'running fallback request', self.fallback_req.action
                self.make_request(self.fallback_req)
        else:
            self._on_second_succeed(response)

        print 'request finished'

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

            for membership in parser.memberships:
                role = membership['MemberRole']

                for member in membership['Members']:
                    try:
                        if 'PassportName' in member:
                            email = member['PassportName'].lower()
                        else:
                            continue

                        if email in self.session.contacts.contacts:
                            contact = self.session.contacts.contacts[email]
                        else:
                            contact = Contact(email)
                            
                            if role == 'Pending':
                                self.session.contacts.pending[email] = contact
                            elif role == 'Reverse':
                                self.session.contacts.reverse[email] = contact
                            else:
                                self.session.contacts.contacts[email] = contact

                        if 'CID' in member:
                            contact.attrs['CID'] = member['CID']

                        if role == 'Pending':
                            contact.attrs['pending'] = True

                            if 'DisplayName' in member:
                                contact.nick = member['DisplayName']
                        elif role == 'Block':
                            contact.blocked = True
                        elif role == 'Reverse':
                            contact.attrs['Reverse'] = True

                    except Exception, error:
                        print 'exception in membership requester: ', str(error)
                    
            DynamicItems(self.session, self.command_queue, 
                self.on_login, self.started_from_cache).start()
        else:
            print 'error requesting membership', response.status
            print response.body
        
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
                        Group(group_name, group_id)

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
                        contact = Contact(email)
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
                
            print 'dynamic finished'

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
                self.session.add_event(Event.EVENT_NICK_CHANGE_SUCCEED, nick)

                if not self.started_from_cache:
                    self.command_queue.put(Command('BLP', params=('BL',)))

                for adl in self.session.contacts.get_adls():
                    self.command_queue.put(Command('ADL', payload=adl))

            self.session.add_event(Event.EVENT_CONTACT_LIST_READY)
            self.session.logger.add_contact_by_group(
                self.session.contacts.contacts, self.session.groups)
        else:
            print 'error requestion dynamic items'

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

            self.session.contacts.contacts[self.account] = Contact(self.account)
            self.session.add_event(Event.EVENT_CONTACT_ADD_SUCCEED, 
                self.account)
        else:
            self.session.add_event(Event.EVENT_CONTACT_ADD_FAILED, self.account)

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

            self.session.add_event(Event.EVENT_CONTACT_REMOVE_SUCCEED, 
                self.account)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_CONTACT_REMOVE_FAILED, 
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
            self.session.add_event(Event.EVENT_NICK_CHANGE_SUCCEED, 
               self.nick)
            self.session.logger.log('nick change', self.account.status, 
                self.nick, self.account)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_NICK_CHANGE_FAILED, self.nick)

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
            self.session.add_event(Event.EVENT_CONTACT_ALIAS_SUCCEED,
                self.account)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_CONTACT_ALIAS_FAILED,
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
            self.session.groups[gid] = Group(self.name, gid)

            self.session.add_event(Event.EVENT_GROUP_ADD_SUCCEED, 
                self.name, gid)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_GROUP_ADD_FAILED, self.name)

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

            self.session.add_event(Event.EVENT_GROUP_REMOVE_SUCCEED, self.gid)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_GROUP_REMOVE_FAILED, self.gid)

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
            self.session.groups[self.gid] = Group(self.name, self.gid)

            self.session.add_event(Event.EVENT_GROUP_RENAME_SUCCEED,
                self.gid, self.name)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_GROUP_RENAME_FAILED,
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

            self.session.add_event(Event.EVENT_GROUP_ADD_CONTACT_SUCCEED,
                self.gid, self.cid)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_GROUP_ADD_CONTACT_FAILED,
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

            self.session.add_event(Event.EVENT_GROUP_REMOVE_CONTACT_SUCCEED, 
                self.gid, self.cid)
        else:
            print '\n', response.body, '\n', request.body, '\n'
            self.session.add_event(Event.EVENT_GROUP_REMOVE_CONTACT_FAILED, 
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
        self.session.add_event(Event.EVENT_CONTACT_BLOCK_FAILED, self.account)

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        self.command_queue.put(Command('ADL', 
            payload=common.build_adl(self.account, 4)))

        self.session.contacts.contacts[self.account].blocked = True

        self.session.add_event(Event.EVENT_CONTACT_BLOCK_SUCCEED, self.account)

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        self.command_queue.put(Command('ADL', 
            payload=common.build_adl(self.account, 2)))
        self.session.add_event(Event.EVENT_CONTACT_BLOCK_FAILED, self.account)

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
        self.session.add_event(Event.EVENT_CONTACT_UNBLOCK_FAILED, self.account)

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        self.command_queue.put(Command('ADL', 
            payload=common.build_adl(self.account, 2)))

        self.session.contacts.contacts[self.account].blocked = False

        self.session.add_event(Event.EVENT_CONTACT_UNBLOCK_SUCCEED,
            self.account)

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        self.command_queue.put(Command('ADL', 
            payload=common.build_adl(self.account, 4)))
        self.session.add_event(Event.EVENT_CONTACT_UNBLOCK_FAILED, self.account)

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
        self.session.add_event(Event.EVENT_CONTACT_MOVE_FAILED,
            self.cid, self.src_gid, self.dest_gid)

    def _on_second_succeed(self, response):
        '''handle the second request if succeeded'''
        self.session.contacts.contacts[self.account]\
            .groups.append(self.dest_gid)
        self.session.contacts.contacts[self.account]\
            .groups.remove(self.src_gid)
        self.session.groups[self.src_gid].contacts.remove(self.account)
        self.session.groups[self.dest_gid].contacts.append(self.account)

        self.session.add_event(Event.EVENT_CONTACT_MOVE_SUCCEED,
            self.cid, self.src_gid, self.dest_gid)

    def _on_second_failed(self, response):
        '''handle the second request if failed'''
        self.session.add_event(Event.EVENT_CONTACT_MOVE_FAILED,
            self.cid, self.src_gid, self.dest_gid)

