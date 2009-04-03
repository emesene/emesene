import xml.sax.saxutils

MSNP_VER = 'MSNP15'
BUILD_VER = '8.0.0792'

PAYLOAD_CMDS = ['GCF', 'MSG', 'UBX', 'NOT']
# the position on params where the number of bytes to read is located
PAYLOAD_POSITION = {
    'GCF' : 0,
    'MSG' : 1,
    'UBX' : 1,
    'NOT' : -1,
}

dic = {
    '\"'    :    '&quot;',
    '\''    :    '&apos;'
}

dic_inv = {
    '&quot;'    :'\"',
    '&apos;'    :'\''
}

def escape(string_):
    '''replace the values on dic keys with the values'''
    return xml.sax.saxutils.escape(string_, dic)

def unescape(string_):
    '''replace the values on dic_inv keys with the values'''
    return xml.sax.saxutils.unescape(string_, dic_inv)

def build_adl(account, type_):
    '''build a xml message to send on ADLs'''
    (name, host) = account.split('@')
    return '<ml><d n="%s"><c n="%s" l="1" t="%d" /></d></ml>' % \
        (host, name, type_)

def get_value_between(string_, start, stop, default=''):
    '''get the value of string_ between start and stop, return default if
    the value cant be extracted. If multiple time appear start on string_
    just the first will be used, if start or stop are not found default will
    be returned'''
    parts = string_.split(start, 1)

    if len(parts) != 2:
        return default

    parts = parts[1].split(stop, 1)
    
    if len(parts) != 2:
        return default

    return parts[0]
