import base64
import calendar
import re
import socket
import struct
import sys
import time
import urllib2
from xml.etree import ElementTree as ET

import funxmpp
import handlers
from sasl import SASL

WHATSAPP_ADDRESS = ('bin-short.whatsapp.net', 5222)

class WAClient:
    def __init__(self, number, passwd, name):
        self.is_connected = False
        self.logged_in = False
        self.socket = None
        self.buffer = ""
        self.events = {'connected': None,
                       'disconnected': None}

        self.handlers = []

        self.message_id_last = 0
        self.message_id_count = 0

        self.sasl = SASL(mechanism='DIGEST-MD5-1', uri="xmpp/s.whatsapp.net",
                realm="s.whatsapp.net")

        self.set_login_info(number, passwd)
        self.set_name(name)

        self._init_handlers()
        self._fix_namespaces()


    def _init_handlers(self):
        """Loads all handlers in the handlers subdirectory.

        A handler needs to be in the handlers/__init__.py's __all__ before it is
        actually used."""

        for name in handlers.__all__:
            # foo_bar to FooBar (CamelCase)
            modname = ''.join(map(str.capitalize, name.split('_')))
            m = __import__('handlers.%s' % name, globals(), None, modname)
            m = getattr(m, modname)
            self.handlers.append(m(self))

            for event in m.EVENTS:
                if event in self.events:
                    raise Exception(("Event '%s' of handler '%s' is already " +
                        "registered.") % (event, name))

                self.events[event] = None


    def _fix_namespaces(self):
        """Fixes etree going all mad about XML namespaces, and messing up our
        data.

        For example:
        >>> elem = ET.fromstring('<foo xmlns="a:namespace" />')
        >>> ET.tostring(elem)
        '<ns0:foo xmlns:ns0="a:namespace" />'
        >>> _fix_namespaces()
        >>> ET.tostring(elem)
        '<foo xmlns="a:namespace" />'"""

        ns = ('urn:ietf:params:xml:ns:xmpp-bind',
              'urn:ietf:params:xml:ns:xmpp-sasl',
              'urn:ietf:params:xml:ns:xmpp-session',
              'urn:ietf:params:xml:ns:xmpp-stanzas',
              'urn:ietf:params:xml:ns:xmpp-streams',
              'urn:xmpp:delay',
              'urn:xmpp:ping',
              'urn:xmpp:receipts',
              'urn:xmpp:whatsapp',
              'urn:xmpp:whatsapp:dirty',
              'urn:xmpp:whatsapp:mms',
              'urn:xmpp:whatsapp:push',
              'jabber:client',
              'jabber:iq:last',
              'jabber:iq:privacy',
              'jabber:x:delay',
              'jabber:x:event',
              'http://jabber.org/protocol/chatstates')

        for n in ns:
            ET._namespace_map[n] = ''

        # Fix the "stream:" things
        ET._namespace_map['http://etherx.jabber.org/streams'] = 'stream'


    def set_login_info(self, number, passwd):
        """Sets the number and password used to login.

        Number must be a mobile phone number including country code, excluding
        any leading zeroes, between 4 and 15 digits long.

        Passwd must be a md5 hash. This normally is the md5 of the reversed imei
        number of the phone."""

        if self.is_connected:
            raise Exception("Already connected!")

        number = self.check_user(number, add_domain=False)

        if not re.match("^[0-9a-f]{32}$", passwd):
            raise ValueError("Passwd must be md5 hash (32 hexadecimal " +
                    "characters), found '%s'." % passwd)

        self.number = number
        self.passwd = passwd
        self.sasl.username = self.number
        self.sasl.password = self.passwd


    def set_name(self, name):
        """Sets the current username.

        This name is not used by Android clients.

        If a connection has already been made, a presence will be sent to notify
        the server."""

        if isinstance(name, unicode):
            name = str(name)

        if not isinstance(name, str):
            raise ValueError("Name should be string, not %s." % type(name))

        if len(name) == 0:
            raise ValueError("Name cannot be empty string.")

        self.name = name

        #TODO: already connected -> send presence


    def check_user(self, user, add_domain=True, group=False):
        """Given a user (either login name or destination of a message), it will
        check and correct it for correctness.

        Any given domain is stripped. A username is valid if it consists of
        between 4 and 15 digits OR is the string 'Server'.

        An optional argument controls whether the result should have
        '@s.whatsapp.net' concatenated at the end."""

        user = str(user)
        if user.find('@') != -1:
            user, group = str(user).split('@')
            group = group == 'g.us'

        if user != 'Server' and not re.match("^\d{4,15}$", user):
            if not group or not re.match("^\d{4,15}-.+$", user):
                raise ValueError("Destination must be between 4 and 15 " +
                        "digits long, found '%s'." % user)

        if add_domain:
            if group:
                user = '%s@g.us' % user
            else:
                user = '%s@s.whatsapp.net' % user

        return user


    def connect(self):
        """Connects to the WhatsApp server and starts the login process."""

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(WHATSAPP_ADDRESS)

        self.is_connected = True
        self.socket.send("WA\x01\x01")

        streamstart = ET.Element('{http://etherx.jabber.org/streams}stream')
        streamstart.set('to', 's.whatsapp.net')
        streamstart.set('resource', 'iPhone-2.8.2-5222')
        self.send(streamstart)

        self.send_features()
        self.send_auth_method()



        recv = self.recv_and_handle(return_single=True)
        if recv.tag != '{http://etherx.jabber.org/streams}stream':
            print "Expected stream:stream, got %s" % recv.tag
        if recv.get('from') != 's.whatsapp.net':
            print "Expected from=\"s.whatsapp.net\", got %s" % recv.get('from')

        recv = self.recv_and_handle(return_single=True, parse_buffer_only=True)
        if recv.tag != '{http://etherx.jabber.org/streams}features':
            print "Expected stream:features, got %s" % recv.tag

        self.trigger_event('connected')

        # Cleanup remaining messages received during call for stream begin.
        self.recv_and_handle(parse_buffer_only=True)


    def disconnect(self):
        """Disconnects from the server."""

        if not self.is_connected:
            raise Exception("Not connected.")

        self.is_connected = False
        self.logged_in = False

        try:
            self.socket.close()
            self.socket.shutdown(0)
        except socket.error:
            pass

        self.trigger_event('disconnected')


    def generate_message_id(self):
        """Generates an unique ID for a new message.

        The id consists of the current timestamp (in seconds), followed by the
        ammount of id's generated with that id, including this one."""

        if int(time.time()) > self.message_id_last:
            self.message_id_last = int(time.time())
            self.message_id_count = 0

        self.message_id_count += 1
        return "%s-%s" % (self.message_id_last, self.message_id_count)



    def generate_iq(self, type, id, xml):
        raise Exception("Not implemented.")


    def generate_message(self, id, to, xml):
        raise Exception("Not implemented.")


    def set_event_handler(self, event, func):
        """Sets the function to be called for a given event.

        If you want to unset a handler, use None as func argument.
        The given event must be known, otherwise an error will be raised."""

        if event not in self.events:
            raise ValueError("Unknown event '%s'" % str(event))

        if not func is None and not callable(func):
            raise ValueError("Function argument is not None and not " +
                "callable (it is of type '%s'." % type(func))

        self.events[event] = func


    def trigger_event(self, event, *args):
        """Triggers an event, so calls the registered handler for an event.

        Intended for internal use, see set_event_handler for registering to
        events."""

        if event not in self.events:
            raise ValueError("Unknown event '%s'" % str(event))

        if self.events[event] is None:
            return

        self.events[event](*args)


    def recv_and_handle(self, return_single=False, parse_buffer_only=False):
        """Receives some data from the server and then tries to parse as much
        messages in the buffer as possible.

        The receiving part of this function will block until there is data to be
        read. Any received data is appended to the current buffer, and then
        we try to extract as many messages from the buffer as possible. For each
        parsed message, the corresponding handler is called.

        It is possible to circumvent the standard behaviour in two ways. You
        probably never need to to that, it is only used internally in special
        situations.

        The return_single flag circumvents the handler part of the the function.
        Any found message is immediately returned. If no messages were found,
        None is returned.

        The parse_buffer_only argument specifies whether the socket should
        receive new data from the server. This can be usefull after a call with
        return_single enabled, to handle the remaining messages in the
        buffer."""

        if not self.is_connected:
            raise Exception("Not connected.")

        if not parse_buffer_only:
            r = self.socket.recv(1024)
            if not r:
                self.disconnect()
                return

            self.buffer += r

        # Smallest message possible has a length of 5 (2 for length, 1 for f8,
        # 1 for f8 lenth, 1 for f8 tagname)
        while len(self.buffer) >= 5:
            msglen = struct.unpack('!H', self.buffer[:2])[0]
            if len(self.buffer) - 2 < msglen:
                return

            msg = self.buffer[2:msglen+2]
            self.buffer = self.buffer[msglen+2:]

            if len(msg) == 0:
                print "BUFCRASH:", msglen, repr(self.buffer)
                self.buf = ''
                return

            try:
                parsed = funxmpp.decode(msg)
                print ' < ', parsed
            except Exception as e:
                print 'Crash in funxmpp.decode', repr(msg), e

            # Stream start needs some special care
            if parsed.split(' ')[0] == '<stream:stream':
                parsed = parsed[:-1] + ' />'

            # Define the stream prefix namespace thing when needed
            if parsed.startswith('<stream:'):
                parsed = re.sub(r'^<stream:([^> ]*)',
                                r'<stream:\1 xmlns:stream="' +
                                    'http://etherx.jabber.org/streams"',
                                parsed)

            xml = ET.fromstring(parsed)

            if return_single:
                return xml

            self._call_handler(xml)


    def _call_handler(self, xml):
        """Calls the handlers matching the given XML tree."""

        tag = xml.tag
        namespace = ""
        if tag.startswith('{'):
            namespace = tag[1:].split('}', 1)[0]
            tag = tag.split('}', 1)[1]

        for handler in self.handlers:
            if (handler.TAG == tag or handler.TAG == "") and \
               (handler.NS == namespace or handler.NS == ""):

                # Now that we passed that test, see if there are any sub filters
                if handler.SUBTAG != "" or handler.SUBNS != "":
                    for subelem in xml:
                        subtag = subelem.tag
                        subnamespace = ""
                        if subtag.startswith('{'):
                            subnamespace = subtag[1:].split('}', 1)[0]
                            subtag = subtag.split('}', 1)[1]

                        if (handler.SUBTAG == subtag or
                            handler.SUBTAG == "") and \
                           (handler.SUBNS == subnamespace or
                            handler.SUBNS == ""):
                            break
                    else:
                        continue

                handler.handle(xml)


    def send(self, data):
        """Sends the given xml data to the WhatsApp server.

        The data is automatically packed in the correct format."""

        if not self.is_connected:
            raise Exception("Cannot send data: Not connected.")

        data = ET.tostring(data)
        data = data.replace(' xmlns:stream="http://etherx.jabber.org/streams"',
                '')
        print ' > ', data
        data = funxmpp.encode(data)
        data = "%s%s" % (struct.pack('!H', len(data)), data)

        self.socket.send(data)
        #print repr(data)


    def send_features(self, features=['receipt_acks']):
        """Sends the given stream features to the server.

        Currently only 'receipt_acks' is supported, which is also the default
        value for the paramter.

        This function should normally only be called once, and is automatically
        called after a stream has been opened."""

        streamfeatures = \
                ET.Element('{http://etherx.jabber.org/streams}features')

        for feature in features:
            ET.SubElement(streamfeatures, feature)

        self.send(streamfeatures)


    def send_auth_method(self, method='DIGEST-MD5-1'):
        """Sends the authentification method to use to the server.

        Currently only 'DIGEST-MD5-1' is supported, which is also the default
        value for the parameter.

        This function should normally only be called once, and is automatically
        called after a stream has been opened."""

        authmethod = ET.Element("{urn:ietf:params:xml:ns:xmpp-sasl}auth")
        authmethod.set('mechanism', method)
        self.send(authmethod)


    def send_auth_response(self, data):
        """Sends the authentification response to the server."""

        resp = ET.Element("{urn:ietf:params:xml:ns:xmpp-sasl}response")
        resp.text = data
        self.send(resp)


    def send_message(self, to, message):
        """Sends a given message to a given user.

        The destination should be in the form of a mobile number, with
        optionally a domain (eg "@s.whatspp.net")."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        messagetext = str(message)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', self.generate_message_id())

        x = ET.SubElement(message, 'x')
        x.set('xmlns', 'jabber:x:event')
        ET.SubElement(x, 'server')

        body = ET.SubElement(message, 'body')
        body.text = messagetext

        self.send(message)


    def send_presence(self, status=None, name=None):
        """Sends a status and/or name to the server.

        Status can be available or unavailable.
        Name is displayed to users using iPhone and other clients (Android does
        not use it).

        Both arguments are optional."""

        if not self.logged_in:
            raise NotLoggedInException()

        presence = ET.Element('presence')
        if status is not None:
            presence.set('type', status)
        if name is not None:
            presence.set('name', name)

        self.send(presence)

    def send_subscribe(self, to):
        """Subscribes to a user, receiving chatstate messages."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        presence = ET.Element('presence')
        presence.set('to', '%s' % to)
        presence.set('type', 'subscribe')

        self.send(presence)

    def send_request_last_seen(self, to):
        """Asks the server how many seconds ago the given user was last seen
        online."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        iq = ET.Element('iq')
        iq.set('to', '%s' % to)
        iq.set('id', self.generate_message_id())
        iq.set('type', 'get')

        query = ET.SubElement(iq, 'query')
        query.set('xmlns', 'jabber:iq:last')

        self.send(iq)


    def send_message_ack(self, to, message_id):
        """Sends a message to the server indicating that a message was received.

        This function is called automatically when a request for it is detected,
        so calling it manually is normally not needed."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', message_id)

        received = ET.SubElement(message, 'received')
        received.set('xmlns', 'urn:xmpp:receipts')

        self.send(message)


    def send_pong(self, ping_id):
        """Sends a pong back to the server in reponse to a ping with a given
        id."""

        pong = ET.Element("iq")
        pong.set('to', 's.whatsapp.net')
        pong.set('type', 'result')
        pong.set('id', ping_id)
        self.send(pong)

    def send_chatstate(self, to, state):
        """Sends the given chatstate to the given user.

        Valid chatstates are composing and paused as specified in XEP-0085.
        Whether the other 3 (active, inactive and gone) are supported is not
        known currently. They don't seem to do anything, but this function
        supports sending them anyway."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        if state not in ('active', 'inactive', 'gone', 'composing', 'paused'):
            raise ValueError("Unknown chatstate: %s" % state)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')

        stateelem = ET.SubElement(message, state)
        stateelem.set('xmlns', 'http://jabber.org/protocol/chatstates')

        self.send(message)


    def send_media_image(self, to, url, preview=None):
        """Sends a given image to a given destination.

        Images are sent via URL's. This function will not upload the image, it
        will only accept already uploaded images.

        Along with the url with the full version (which the other client app
        automatically downloads), a preview image can be given which is
        displayed in the conversation itself."""

        #TODO: fetch url and get preview when not given?

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', self.generate_message_id())

        x = ET.SubElement(message, 'x')
        x.set('xmlns', 'jabber:x:event')
        ET.SubElement(x, 'server')

        media = ET.SubElement(message, 'media')
        media.set('xmlns', 'urn:xmpp:whatsapp:mms')
        media.set('type', 'image')
        media.set('url', url)
        media.set('file', url.split('/')[-1])

        if preview is not None:
            media.text = preview

        self.send(message)


    def send_media_audio(self, to, url, size=None):
        """Sends a given audio clip to a given destination.

        Audio clips are sent via URL's. This function will not upload the audio
        clip, it will only accept already uploaded clips."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', self.generate_message_id())

        x = ET.SubElement(message, 'x')
        x.set('xmlns', 'jabber:x:event')
        ET.SubElement(x, 'server')

        media = ET.SubElement(message, 'media')
        media.set('xmlns', 'urn:xmpp:whatsapp:mms')
        media.set('type', 'audio')
        media.set('url', url)
        media.set('file', url.split('/')[-1])
        if size is not None:
            media.set('size', size)

        self.send(message)


    def send_media_video(self, to,  url, preview=None, size=None):
        """Sends a given video to a given destination.

        Videos are sent via URL's. This function will not upload the video, it
        will only accept already uploaded videos.

        A preview image can be given which is displayed in the conversation
        itself."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', self.generate_message_id())

        x = ET.SubElement(message, 'x')
        x.set('xmlns', 'jabber:x:event')
        ET.SubElement(x, 'server')

        media = ET.SubElement(message, 'media')
        media.set('xmlns', 'urn:xmpp:whatsapp:mms')
        media.set('type', 'video')
        media.set('url', url)
        media.set('file', url.split('/')[-1])
        if size is not None:
            media.set('size', size)

        if preview is not None:
            media.text = preview

        self.send(message)


    def send_media_location(self, to, latitude, longitude, name=None, url=None):
        """Sends a location to a given destination.

        A location is always specified by a latitude and longitude. Optionally,
        a name and url can be given, if you are sending a 'point of interest'.

        A preview is also generated and sent. This is a 100x100 image from
        Google Maps. This function will simply use the google maps static api.
        WhatsApp does this too, but to get rid of the watermark, it requests a
        170x170 image, and cuts out the center. This function will not do that,
        and thus include a Google watermark in the corner."""

        if not self.logged_in:
            raise NotLoggedInException()

        prevurl = ("http://maps.google.com/maps/api/staticmap?" +
                    "center=%(latitude)s,%(longitude)s&zoom=15&size=100x100&" +
                    "sensor=false&format=jpg&mobile=true&" +
                    "markers=color:red%%7Csize:mid%%7C" +
                    "%(latitude)s,%(longitude)s") % \
                    {'latitude': latitude, 'longitude': longitude}

        preview = base64.b64encode(urllib2.urlopen(prevurl).read())

        to = self.check_user(to)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', self.generate_message_id())

        x = ET.SubElement(message, 'x')
        x.set('xmlns', 'jabber:x:event')
        ET.SubElement(x, 'server')

        media = ET.SubElement(message, 'media')
        media.set('xmlns', 'urn:xmpp:whatsapp:mms')
        media.set('type', 'location')
        media.set('latitude', latitude)
        media.set('longitude', longitude)

        if name is not None:
            media.set('name', name)
        if url is not None:
            media.set('url', url)

        media.text = preview

        self.send(message)



    def send_media_vcard(self, to, name, content):
        """Sends soms vCard data to a given destination.

        Name denotes the name of the vCard, content is the raw vCard data.
        WhatsApp supports vCard v3.0."""

        if not self.logged_in:
            raise NotLoggedInException()

        to = self.check_user(to)

        message = ET.Element('message')
        message.set('to', '%s' % to)
        message.set('type', 'chat')
        message.set('id', self.generate_message_id())

        x = ET.SubElement(message, 'x')
        x.set('xmlns', 'jabber:x:event')
        ET.SubElement(x, 'server')

        media = ET.SubElement(message, 'media')
        media.set('xmlns', 'urn:xmpp:whatsapp:mms')
        media.set('type', 'vcard')
        media.set('encoding', 'text')

        vcard = ET.SubElement(media, 'vcard')
        vcard.set('name', name)

        vcard.text = content

        self.send(message)


    def send_request_group_info(self, group):
        """Queries the server for info about a given group."""

        if not self.logged_in:
            raise NotLoggedInException()

        group = self.check_user(group)

        iq = ET.Element('iq')
        iq.set('to', '%s' % group)
        iq.set('id', self.generate_message_id())
        iq.set('type', 'get')

        query = ET.SubElement(iq, 'query')
        query.set('xmlns', 'w:g')

        self.send(iq)


    def send_request_group_participants(self, group):
        """Retrieves participants for a given group."""

        if not self.logged_in:
            raise NotLoggedInException()

        group = self.check_user(group)

        iq = ET.Element('iq')
        iq.set('to', '%s' % group)
        iq.set('id', self.generate_message_id())
        iq.set('type', 'get')

        lst = ET.SubElement(iq, 'list')
        lst.set('xmlns', 'w:g')

        self.send(iq)


    def parse_xmpp_time(self, stamp):
        """Returns a datetime object given a date/time string following the
        XEP-0082 format.

        The returned time object will be in local time. This implementation
        ignores the timezone part of the given string, and assumes it is UTC."""

        # Strip timezone and force UTC (HACK)
        stamp = stamp[:19] + "UTC"

        utctime = time.strptime(stamp, '%Y-%m-%dT%H:%M:%S%Z')
        secs = calendar.timegm(utctime)
        localtime = time.localtime(secs)

        return localtime



class NotLoggedInException(Exception):
    pass
