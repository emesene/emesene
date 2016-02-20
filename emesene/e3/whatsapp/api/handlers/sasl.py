from base import BaseHandler
import sasl

class Sasl(BaseHandler):
    NS = "urn:ietf:params:xml:ns:xmpp-sasl"

    EVENTS = ['login_succeeded', 'login_failed']

    def handle(self, xml):
        tag = xml.tag.split('}', 1)[-1]

        if tag == 'challenge':
            print "SASL CHALLENGE:", xml.text

            resp = self.waclient.sasl.get_response(xml.text)
            self.waclient.send_auth_response(resp)
        elif tag == 'failure':
            self.waclient.trigger_event('login_failed')
            self.waclient.disconnect()
        elif tag == 'success':
            #TODO: error when account expired?
            self.waclient.logged_in = True
            self.waclient.send_presence(status='available',
                    name=self.waclient.name)

            self.waclient.trigger_event('login_succeeded', xml.get('status'),
                    xml.get('kind'), xml.get('creation'), xml.get('expiration'))

        else:
            print "UNKNOWN SASL TAG:", tag
