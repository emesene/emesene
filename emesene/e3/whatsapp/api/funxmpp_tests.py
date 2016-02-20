#!/usr/bin/env python2
#
# Unittests for funxmpp.py
#

import unittest

import funxmpp

class TestFunXmpp(unittest.TestCase):
    def test_encode(self):
        """Tests the encode function."""

        data = (
           ('<message from="01234567890@s.whatsapp.net" ' +
                     'id="1339831077-7" ' +
                     'type="chat" ' +
                     't="1339848755">' +
                '<notify xmlns="urn:xmpp:whatsapp" ' +
                        'name="Koen" />' +
                '<request xmlns="urn:xmpp:receipts" />' +
                '<body>Hello</body>' +
            '</message>',
            '\xf8\x0a\x5d\x38\xfa\xfc\x0b01234567890\x8a' +
                        '\x43\xfc\x0c1339831077-7' +
                        '\xa2\x1b' +
                        '\x9d\xfc\x0a1339848755' +
                '\xf8\x03' +
                    '\xf8\x05\x65\xbd\xae' +
                                '\x61\xfc\x04Koen' +
                    '\xf8\x03\x83\xbd\xad' +
                    '\xf8\x02\x16' +
                        '\xfc\x05Hello'),

           ("<message>%s</message>" % ("x" * 255),
            "\xf8\x02\x5d\xfc\xff%s" % ("x" * 255)),

           ("<message>%s</message>" % ("x" * 1025),
            "\xf8\x02\x5d\xfd\x00\x04\x01%s" % ("x" * 1025)),

           ('<stream:stream to="s.whatsapp.net" ' +
                'resource="iPhone-2.6.9-5222" />',
            '\xf8\x05\x01\xa0\x8a\x84\xfc\x11iPhone-2.6.9-5222'),

           ('<stream:stream to="s.whatsapp.net" resource="iPhone-2.6.9-5222">',
            '\xf8\x05\x01\xa0\x8a\x84\xfc\x11iPhone-2.6.9-5222'),

           ('<stream:features><receipt_acks /></stream:features>',
            '\xf8\x02\x96\xf8\x01\xf8\x01\x7e'),

           ('<message to="00622222222@s.whatsapp.net" ' +
                     'type="chat" ' +
                     'id="1343676064-1">' +
                '<x xmlns="jabber:x:event">' +
                    '<server />' +
                '</x>' +
                '<body>' +
                    'Hi there!' +
                '</body>' +
            '</message>',
            '\xf8\x08]\xa0\xfa\xfc\x0b00622222222\x8a' +
                     '\xa2\x1b' +
                     'C\xfc\x0c1343676064-1' +
                '\xf8\x02' +
                    '\xf8\x04\xba\xbdO' +
                        '\xf8\x01' +
                            '\xf8\x01\x8c' +
                    '\xf8\x02\x16' +
                        '\xfc\x09Hi there!')
        )

        for o, r in data:
            e = funxmpp.encode(o)

            self.assertEqual(e, r,
                "Encoding incorrect:\n%s\n%s" % (repr(e), repr(r)))

    def test_decode(self):
        """Tests the decode function."""

        data = (
            ('\xf8\x01\xfc\x03foo',
             '<foo />'),

            ('\xf8\x03\x01\x38\x8a',
             '<stream:stream from="s.whatsapp.net">'),

            ('\xf8\x08]\xa0\xfa\xfc\x0b12345678912\x8a\xa2\x1bC\xfc\x0c' +
                '1343064803-1\xf8\x02\xf8\x04\xba\xbdO\xf8\x01\xf8\x01\x8c' +
                '\xf8\x02\x16\xfc\x04Okay',
             '<message to="12345678912@s.whatsapp.net" type="chat" ' +
                'id="1343064803-1"><x xmlns="jabber:x:event"><server /></x>' +
                '<body>Okay</body></message>')
        )


        for o, r in data:
            d = funxmpp.decode(o)

            self.assertEqual(d, r,
                "Encoding incorrect:\n%s\n%s" % (repr(d), repr(r)))

    def test_both(self):
        """Sees if a encode followed by a decode results in the same data."""

        data = ['<foo x="y"><poke name="stuff" /><another thing="yay" />' +
                    '<body>bar</body></foo>',

                '<message from="01234567890@s.whatsapp.net" ' +
                             'id="1339831077-7" ' +
                             'type="chat" ' +
                             't="1339848755">' +
                    '<notify xmlns="urn:xmpp:whatsapp" ' +
                            'name="Koen" />' +
                    '<request xmlns="urn:xmpp:receipts" />' +
                    '<body>Hello</body>' +
                '</message>',

                '<iq from="1234@s.whatsapp.net" id="1" type="error">' +
                    '<error code="404" type="cancel">' +
                    '<item-not-found ' +
                        'xmlns="urn:ietf:params:xml:ns:xmpp-stanzas" />' +
                    '</error></iq>']

        for t in data:
            self.assertEqual(t, funxmpp.decode(funxmpp.encode(t)))

if __name__ == '__main__':
    unittest.main()
