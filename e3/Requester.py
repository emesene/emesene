'''defines objects that make requests to the server on a thread'''

import urllib
import httplib
import threading

import XmlParser
import XmlManager
import protocol.base.Event as Event
import protocol.base.Group as Group
import protocol.base.Contact as Contact

from Command import Command

def build_adl(account, type_):
    '''build a xml message to send on ADLs'''
    (name, host) = account.split('@')
    return '<ml><d n="%s"><c n="%s" l="1" t="%d" /></d></ml>' % \
        (host, name, type_)

class Requester(threading.Thread):
    '''a class that makes a soap request on a thread'''

    def __init__(self, session, action, host, port, path, body):
        '''class constructor, session is the session object'''
        threading.Thread.__init__(self)

        self.session = session

        self.action = action
        self.host = host
        self.port = port
        self.path = path
        self.body = body

        self.response = None
        self.status = None
        self.reason = None

    def run(self):
        '''main method of the thread, make the request and handle the response
        '''
        print 'running request', self.action
        self.make_request()
        self.handle_response()
        print 'request finished'

    def make_request(self):
        '''send the soap request to the server'''
        headers = {
            'SOAPAction': self.action,
            'Content-Type': 'text/xml; charset=utf-8',
            'Cookie': 'MSPAuth=' + self.session.extras['MSPAuth'][:-2] + \
              ';MSPProf=' + self.session.extras['MSPProf'],
            'Host': self.host,
            'Content-Length': str(len(self.body)),
            'User-Agent': 'MSN Explorer/9.0 (MSN 8.0; TmstmpExt)',
            'Connection': 'Keep-Alive',
            'Cache-Control': 'no-cache',
        }
        
        #print headers
        conn = None
        response = None
        
        if self.port == 443:
            conn = httplib.HTTPSConnection(self.host, self.port)  
        else:
            conn = httplib.HTTPConnection(self.host, self.port)
        
        conn.request('POST', self.path, self.body, headers)
        response = conn.getresponse()
        
        self.response = response.read()
        self.status = response.status
        self.reason = response.reason

    def handle_response(self):
        '''override this to do something with the response'''
        pass

class Membership(Requester):
    '''make the request to get the membership list'''
    def __init__(self, session, command_queue, on_login):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to be
        sent, if on_login is true, then some commands need to be
        sent in order to inform the server about our contacts'''
        Requester.__init__(self, session, 
          'http://www.msn.com/webservices/AddressBook/FindMembership',
          'contacts.msn.com', 443, '/abservice/SharingService.asmx',
          XmlManager.get('membership') % session.extras['contacts.msn.com']\
                                  ['security'].replace('&', '&amp;') + '\r\n')

        self.command_queue = command_queue
        self.on_login = on_login

    def handle_response(self):
        '''handle the response'''
        if self.status == 200:
            parser = XmlParser.MembershipParser(self.response)

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
                self.on_login).start()
        else:
            print 'error requesting membership', self.status
            print self.response
        
class DynamicItems(Requester):
    '''make the request to get the dynamic items'''
    def __init__(self, session, command_queue, on_login):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to be
        sent, if on_login is true, then some commands need to be
        sent in order to inform the server about our contacts'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABFindAll',
          'contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('dynamicitems') % session.extras['contacts.msn.com']\
                                            ['security'].replace('&', '&amp;'))

        self.command_queue = command_queue
        self.on_login = on_login

    def handle_response(self):
        '''handle the response'''
        if self.status == 200:
            parser = XmlParser.DynamicParser(self.response)
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
                    email = contact_dict['passportName']
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
                    self.session.groups[guid].contacts.append(
                        contact.account)


                for ann in contact_dict['Annotations']:
                    if ann.get('Name', None) == 'AB.NickName':
                        contact.alias = urllib.unquote(ann['Value'])
                        break

                contact.nick = urllib.unquote(contact_dict.get('displayName', 
                    contact.account))

                contact.attrs['mobile'] = \
                    contact_dict.get('isMobileIMEnabled', None) == 'true'

                contact.attrs['space'] = \
                    contact_dict.get('hasSpace', None) == 'true'
                
            print 'dynamic finished'

            # get our nick
            try:
                nick = self.response.split('<contactType>Me</contactType>')\
                    [1].split('</displayName>')[0].split('<displayName>')[1]
                nick = nick.replace('&apos;', '\'').replace('&quot;', '"')
            except IndexError:
                nick = self.session.contacts.me.account

            self.session.contacts.me.nick = nick

            if self.on_login:
                # set our nick
                nick = urllib.quote(nick)
                self.command_queue.put(Command('PRP', params=('MFN', nick)))
                self.command_queue.put(Command('BLP', params=('BL',)))
                for adl in self.session.contacts.get_adls():
                    self.command_queue.put(Command('ADL', payload=adl))

            self.session.events.put(Event(Event.EVENT_CONTACT_LIST_READY))
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
          XmlManager.get('addcontact') % \
          (session.extras['contacts.msn.com']['security'].replace('&', '&amp;'),
           account)

        self.account = account
        self.command_queue = command_queue

    def handle_response(self):
        '''handle the response'''
        if self.status == 200:
            self.command_queue.put(Command('ADL', 
                payload=build_adl(self.account, 1)))
            self.command_queue.put(Command('ADL', 
                payload=build_adl(self.account, 2)))
            self.session.events.put(Event(Event.EVENT_CONTACT_ADD_SUCCEED, 
                self.account))
        else:
            self.session.events.put(Event(Event.EVENT_CONTACT_ADD_FAILED, 
                self.account))

class RemoveContact(Requester):
    '''make the request to remove a contact to the contact list'''
    def __init__(self, session, cid, account, command_queue):
        '''command_queue is a reference to a queue that is used
        by the worker to get commands that other threads need to 
        send'''
        Requester.__init__(self, session,
          'http://www.msn.com/webservices/AddressBook/ABContactDelete',
          'omega.contacts.msn.com', 443, '/abservice/abservice.asmx',
          XmlManager.get('addcontact') % \
          (session.extras['contacts.msn.com']['security'].replace('&', '&amp;'),
           account)

        self.cid = cid
        self.account = account
        self.command_queue = command_queue

    def handle_response(self):
        '''handle the response'''
        if self.status == 200:
            self.session.events.put(Event(Event.EVENT_CONTACT_REMOVE_SUCCEED, 
                self.account))
        else:
            self.session.events.put(Event(Event.EVENT_CONTACT_REMOVE_FAILED, 
                self.account))

