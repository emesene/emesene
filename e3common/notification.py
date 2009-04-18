def _dummy_notify(title, message, image_path):
    """
    notify message to the user
    """
    print title
    print '  ', message

try:
    import gobject
    import pynotify

    if not pynotify.init("emesene 2"):
        notify = _dummy_notify

    def notify(title, text, image_path=None):

        notification = pynotify.Notification(title, text)

        if image_path:
            notification.set_icon_from_file(image_path)

        try:
            notification.show()
        except gobject.GError:
            return
except ImportError:
    notify = _dummy_notify
