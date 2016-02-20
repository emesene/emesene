import urllib2

# TODO:
#  - Parse responses, errors
#  - Generate token for sms/voice code request

class RegisterDevice:
    """Allows you to register a new device to WhatsApp or change the password on
    a currently registered number.

    Note that if you reset a password, the official client won't be able to
    login until you reset it again. This is because the password is normally
    derived from an unique number assiciated with the phone.

    Note that this module DOES NOT work correctly! The function that should
    request the sms does not work, always gives an error. This is because
    WhatsApp expects a certain token (an MD5 hash) generated using the mobile
    number. I currently do not know how this is generated.

    The other functions DO work correctly. It is still possible to change the
    password, as long as you have the 3-digit verification code.

    Obtaining that can be done by using for example the official Android client.
    A simple way that does not require any smartphone is using BlueStacks
    (http://bluestacks.com/). Install WhatsApp inside BlueStacks and enter your
    normal number. After about 10 minutes, you should receive an sms with your
    code."""

    def __init__(self, mobile_number):
        self.mobile_number = mobile_number

        self.user_agent = \
                "WhatsApp/2.8.1504 Android/2.3.4 Device/HTC-HTC_Desire"

        self.lg = "zz" # en
        self.lc = "ZZ" # US
        self.mnc = "000"
        self.mcc = "000"
        self.method = "sms"
        self.reason = "self-send-jailbroken"
        self.token = "..."
        self.imsi = "00000000000000"


    def exists(self, passwd):
        """Queries the WhatsApp server whether a number is already registred
        using the given password."""

        """
        <?xml version="1.0" encoding="UTF-8"?>
        <exist>
        <response status="ok" result="00611111111"/>
        </exist>


        <?xml version="1.0" encoding="UTF-8"?>
        <exist>
        <response status="fail" result="incorrect"/>
        </exist>
        """
        url = ("https://r.whatsapp.net/v1/exist.php?cc=%s&in=%s&udid=%s") % \
                (self.mobile_number[:2], self.mobile_number[2:], passwd)

        headers = {'User-agent': self.user_agent}

        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req).read()

        print response


    def send_sms(self):
        """Sends an SMS to the set number with the verification code needed to
        change the password.

        Does currently NOT work! See the documentation of this class why and for
        solutions."""

        """
        <?xml version="1.0" encoding="UTF-8"?>
        <code>
        <response status="success-sent" result="60"/>
        </code>


        <?xml version="1.0" encoding="UTF-8"?>
        <code>
        <response status="fail-too-recent" result="180"/>
        </code>

        <?xml version="1.0" encoding="UTF-8"?>
        <code>
        <response status="fail-too-many"/>
        </code>
        """

        raise Exception("Not working! See RegisterDevice documentation.")

        url = ("https://r.whatsapp.net/v1/code.php?cc=%s&to=%s&in=%s&lg=%s" +
                    "&lc=%s&mnc=%s&mcc=%s&method=%s&reason=%s&token=%s") % \
                (self.mobile_number[:2], self.mobile_number,
                 self.mobile_number[2:], self.lg, self.lc, self.mnc, self.mcc,
                 self.method, self.reason, self.token)

        print url

        headers = {'User-agent': self.user_agent}

        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req).read()

        print response

    def set_password(self, code, password):
        """Changes the password of the set number to the given value, with the
        given verification code.

        To obtain the verification code, call send_sms.
        WhatsApp itself sets the password to the md5 has of the reversed IMEI
        number of your phone."""

        """
        <?xml version="1.0" encoding="UTF-8"?>
        <register>
        <response status="ok" login="00611111111" result="new"/>
        </register>

        <?xml version="1.0" encoding="UTF-8"?>
        <register>
        <response status="mismatch" login="00611111111"
                result="me=00611111111 code=123" />
        </register>
        """

        url = ("https://r.whatsapp.net/v1/register.php?cc=%s&in=%s&udid=%s" +
                "&code=%s") % \
                (self.mobile_number[:2], self.mobile_number[2:], password,
                 code)

        headers = {'User-agent': self.user_agent}

        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req).read()

        print response


if __name__ == '__main__':
    from hashlib import md5

    num = raw_input("Mobile number with country code\n > ")
    passwd = raw_input("Password (will be reversed and md5'd)\n > ")

    passwd = md5(passwd[::-1]).hexdigest()

    print "Using number", num, "with password", passwd

    reg = RegisterDevice(num)
    reg.exists(passwd)

    # Not working!
    #reg.send_sms()

    code = raw_input("SMS verification code\n > ")

    reg.set_password(code, passwd)




