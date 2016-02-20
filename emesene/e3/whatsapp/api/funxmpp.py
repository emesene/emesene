#!/usr/bin/env python2
#
# funxmpp.py  -  FunXMPP encoder and decoder
#
# Translates between normal XMPP messages and WhatsApp's FunXMPP.
#

# Lookup table for common xmpp keywords. Extracted from the apk.
funxmpp_enc = [None, "stream:stream", None, None, None, "1", "1.0", "ack",
"action", "active", "add", "all", "allow", "apple", "audio", "auth", "author",
"available", "bad-request", "base64", "Bell.caf", "bind", "body", "Boing.caf",
"cancel", "category", "challenge", "chat", "clean", "code", "composing",
"config", "conflict", "contacts", "create", "creation", "default", "delay",
"delete", "delivered", "deny", "DIGEST-MD5", "DIGEST-MD5-1", "dirty", "en",
"enable", "encoding", "error", "expiration", "expired", "failure", "false",
"favorites", "feature", "field", "free", "from", "g.us", "get", "Glass.caf",
"google", "group", "groups", "g_sound", "Harp.caf",
"http://etherx.jabber.org/streams", "http://jabber.org/protocol/chatstates",
"id", "image", "img", "inactive", "internal-server-error", "iq", "item",
"item-not-found", "jabber:client", "jabber:iq:last", "jabber:iq:privacy",
"jabber:x:delay", "jabber:x:event", "jid", "jid-malformed", "kind", "leave",
"leave-all", "list", "location", "max_groups", "max_participants",
"max_subject", "mechanism", "mechanisms", "media", "message", "message_acks",
"missing", "modify", "name", "not-acceptable", "not-allowed", "not-authorized",
"notify", "Offline Storage", "order", "owner", "owning", "paid", "participant",
"participants", "participating", "fail", "paused", "picture", "ping", "PLAIN",
"platform", "presence", "preview", "probe", "prop", "props", "p_o", "p_t",
"query", "raw", "receipt", "receipt_acks", "received", "relay", "remove",
"Replaced by new connection", "request", "resource", "resource-constraint",
"response", "result", "retry", "rim", "s.whatsapp.net", "seconds", "server",
"session", "set", "show", "sid", "sound", "stamp", "starttls", "status",
"stream:error", "stream:features", "subject", "subscribe", "success",
"system-shutdown", "s_o", "s_t", "t", "TimePassing.caf", "timestamp", "to",
"Tri-tone.caf", "type", "unavailable", "uri", "url",
"urn:ietf:params:xml:ns:xmpp-bind", "urn:ietf:params:xml:ns:xmpp-sasl",
"urn:ietf:params:xml:ns:xmpp-session", "urn:ietf:params:xml:ns:xmpp-stanzas",
"urn:ietf:params:xml:ns:xmpp-streams", "urn:xmpp:delay", "urn:xmpp:ping",
"urn:xmpp:receipts", "urn:xmpp:whatsapp", "urn:xmpp:whatsapp:dirty",
"urn:xmpp:whatsapp:mms", "urn:xmpp:whatsapp:push", "value", "vcard", "version",
"video", "w", "w:g", "w:p:r", "wait", "x", "xml-not-well-formed", "xml:lang",
"xmlns", "xmlns:stream", "Xylophone.caf", "account", "digest", "g_notify",
"method", "password", "registration", "stat", "text", "user", "username",
"event", "latitude", "longitude", "true", "after", "before", "broadcast",
"count", "features", "first", "index", "invalid-mechanism", "last", "max",
"offline", "proceed", "required", "sync", "elapsed", "ip", "microsoft", "mute",
"nokia", "off", "pin", "pop_mean_time", "pop_plus_minus", "port", "reason",
"server-error", "silent", "timeout", "lc", "lg", "bad-protocol", "none",
"remote-server-timeout", "service-unavailable", "w:p", "w:profile:picture",
"notification"]

def decode(message):
    """Translates FunXMPP into normal XMPP."""

    ret = decode_with_len(message)[0]

    # The opening tag (<stream:stream ...>) has no closing (the entire
    # conversation is wrapped inside it, see XMPP Core RFC). Replace the ".. />"
    # by a "..>" if the tagname is \x01 (stream:stream).
    if message[2] == '\x01':
        ret = ret[:-3] + '>'

    return ret

def decode_with_len(message):
    """Translates FunXMPP into normal XMPP while also returning the length in
    number of bytes used for the decoding.

    This function is used internally for recursively parsing the entire
    structure."""

    if message[0] != '\xf8':
        raise ValueError("No XML tag was found at beginning. First character " +
            "should be '\xf8', found %s" % repr(message[0]))


    size = ord(message[1])

    if message[2] == '\xf8':
        # We are a list of xml tags. We ourselves are NOT a tag.

        ret = ""
        pos = 2
        for i in range(size):
            m, l = decode_with_len(message[pos:])
            ret += m
            pos += l

        return ret, pos

    ret = '<'
    tagname, l = get_val_decode(message[2:])
    ret += tagname
    attribs = (size - 2 + (size & 1)) / 2

    pos = 2 + l
    for i in range(attribs):
        ret += " "
        val, valbytes = get_val_decode(message[pos:])
        ret += val
        pos += valbytes

        val, valbytes = get_val_decode(message[pos:])

        ret += "=\"%s\"" % val
        pos += valbytes


    if size % 2 == 0:
        # Tag with content
        ret += '>'
        if message[pos] == '\xf8':
            m, l = decode_with_len(message[pos:])
            ret += m
            pos += l
        else:
            val, l = get_val_decode(message[pos:])
            ret += val
            pos += l
        ret += '</%s>' % tagname
    else:
        # <.../>
        ret += ' />'

    return ret, pos

def get_val_decode(message):
    """Returns a single item for the decoding process, including its length in
    original bytes.

    Possible items include JID pair, string, long string and a keyword byte."""

    if message[0] == '\xfa':
        # JID_PAIR, val1@val2
        val1, vallen1 = get_val_decode(message[1:])
        val2, vallen2 = get_val_decode(message[1+vallen1:])
        return "%s@%s" % (val1, val2), vallen1 + vallen2 + 1
    elif message[0] == '\xfc':
        # String, length in next byte
        vallen = ord(message[1])
        val = message[2:2+vallen]

        return val, vallen+2
    elif message[0] == '\xfd':
        # String, length in next 3 bytes (big endian)
        vallen = (ord(message[1]) << 16) | \
                 (ord(message[2]) << 8) | \
                 (ord(message[3]) << 0)
        val = message[4:4+vallen]

        return val, vallen+4
    else:
        ind = ord(message[0])
        if ind < 0x05 and ind != 0x01:
            print "WARNING, get_val enc reading", ind
            return "0", 1
        if ind > 0xf2:
            raise Exception("Structure char not implemented: 0x%02x" % ind)
        return funxmpp_enc[ind], 1

def encode(message):
    """Encodes xmpp into funxmpp."""

    # The opening tag (<stream:stream ...>) has no closing (the entire
    # conversation is wrapped inside it, see XMPP Core RFC). Hack that into the
    # function by feeding a <stream:stream />.
    if message.startswith('<stream:stream'):
        message = message[:-1] + ' />'

    return encode_with_len(message)[0]

def encode_with_len(message):
    """Encodes xmpp into funxmpp, also returning the length of the parsed tag.

    Used for recusively parsing the XML tree."""

    if message[0] != '<':
        raise ValueError("No XML tag was found at beginning. First character " +
            "should be '<', found %s" % repr(message))

    tagname = message[1:].split(' ')[0].split('>')[0]
    hasclosing = True

    #
    # First, parse the XML. Determine attributes of this tag, and where its
    # contents start (if any).
    #

    attrs, vals = [], []
    hasesc = False
    inkey = True
    tmp = ""
    pos = 1 + len(tagname)
    spos = pos
    for l in message[spos:]:
        pos += 1
        if inkey:
            if l == '=':
                attrs.append(tmp)
                tmp = ""
            elif l == '"':
                inkey = False
            elif l == ' ':
                pass
            elif l == '/':
                hasclosing = False
            elif l == '>':
                break
            else:
                tmp += l
        else:
            if l == '\\':
                if hasesc:
                    tmp += '\\'
                    hasesc = False
                else:
                    hasesc = True
            elif l == '"':
                if hasesc:
                    tmp += '"'
                else:
                    vals.append(tmp)
                    tmp = ''
                    inkey = True
            else:
                tmp += l

    if not inkey:
        raise Exception("End of string while in value: %s" % repr(message))

    #
    # Now parse the contents of the tag, if any.
    #

    cont = []
    if hasclosing:
        # Parse content of this tag (either subtags of string)
        if message[pos] == '<':
            # Parse all subtags recursively
            while len(message) > pos + 3:
                if message[pos+1] == '/':
                    # Add length closing tag
                    pos += 3 + len(tagname)
                    break
                c, l = encode_with_len(message[pos:])
                cont.append(c)
                pos += l
        else:
            # String
            s = message[pos:].split('<')[0]
            pos += len(s)
            cont.append(get_val_encode(s))

    if len(cont) > 255:
        raise Exception("Sub tags more than 255, cannot encode in one byte: " +
            "%d" % len(cont))

    #
    # Finally, pack all found data in FunXMPP.
    #

    ret = repr(zip(attrs, vals))
    ret += '{%s}' % ','.join(cont)

    taglen = 1 # Tag name
    taglen += len(attrs) * 2 # Keys and values
    if len(cont) > 0:
        taglen += 1

    if taglen > 255:
        raise Exception("Tag length more than 255, cannot encode in one " +
            "byte: %d" % taglen)

    ret = "\xf8%s" % chr(taglen)
    ret += get_val_encode(tagname)

    # Flatten list
    t = [i for s in zip(attrs, vals) for i in s]
    ret += ''.join(map(get_val_encode, t))

    if len(cont) > 0:
        if cont[0].startswith('\xf8'):
            ret += "\xf8%s" % chr(len(cont))
        ret += ''.join(cont)


    return ret, pos

def get_val_encode(message):
    """Returns the xmpp notation for a string.

    This includes a single byte if the string is found in the keyword map.
    Otherwise, the result will be a string literal object or JID pair."""

    if message in funxmpp_enc:
        return chr(funxmpp_enc.index(message))
    elif message.endswith('@s.whatsapp.net'):
    #elif message.find('@') > -1:
        # JID pair
        # TODO: hacked in so this doesn't occur all the time...
        n, h = message.split('@', 1)
        return "\xfa%s%s" % (get_val_encode(n), get_val_encode(h))
    elif len(message) <= 0xff:
        # Ascii sequence with 1 byte length
        return '\xfc%s%s' % (chr(len(message)), message)
    elif len(message) <= 0xffffff:
        # Ascii sequence with 3 bytes length (big endian)
        return '\xfd%s%s%s%s' % (chr((len(message) & 0xff0000) >> 16),
                                 chr((len(message) & 0x00ff00) >> 8),
                                 chr((len(message) & 0x0000ff)), message)
    else:
        raise Exception("Cannot encode %s" % repr(message))
