import gui

NAME = 'ThemeNotificationImage'
DESCRIPTION = 'Returns an image path depending on current theme'
AUTHORS = ['Andrea Stagi', 'arielj']
WEBSITE = 'www.emesene.org'

def ThemeNotificationImage(picture, const_value):
    ''' decides which theme picture to use '''

    if picture:
        if picture.startswith("file://"):
            return picture
    if const_value == 'mail-received':
        return "file://" + gui.theme.image_theme.email
    elif const_value == 'file-transf-completed':
        return "file://" + gui.theme.image_theme.transfer_success
    elif const_value == 'file-transf-canceled':
        return "file://" + gui.theme.image_theme.transfer_unsuccess
    elif const_value == 'message-im':
        return "file://" + gui.theme.image_theme.user_def_imagetool
    else:
        return "file://" + gui.theme.image_theme.user_def_imagetool

