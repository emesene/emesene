NAME = 'DummyNotificationImage'
DESCRIPTION = 'Returns the same image path, to use insted of ThemeNotificationImage'
AUTHORS = ['arielj']
WEBSITE = 'www.emesene.org'

def DummyNotificationImage(picture, const_value):
    ''' does nothing, to use instead of ThemeNotificationImage '''
    return picture
