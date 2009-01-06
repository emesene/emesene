
# JID Escaping XEP-0106 for the xmpppy based transports written by Norman Rasmussen

"""This file is the XEP-0106 commands.

Implemented commands as follows:

4.2 Encode : Encoding Transformation
4.3 Decode : Decoding Transformation


"""

xep0106mapping = [
	[' ' ,'20'],
	['"' ,'22'],
	['&' ,'26'],
	['\'','27'],
	['/' ,'2f'],
	[':' ,'3a'],
	['<' ,'3c'],
	['>' ,'3e'],
	['@' ,'40']]

def JIDEncode(str):
	str = str.replace('\\5c', '\\5c5c')
	for each in xep0106mapping:
		str = str.replace('\\' + each[1], '\\5c' + each[1])
	for each in xep0106mapping:
		str = str.replace(each[0], '\\' + each[1])
	return str
    
def JIDDecode(str):
	for each in xep0106mapping:
		str = str.replace('\\' + each[1], each[0])
	return str.replace('\\5c', '\\')
