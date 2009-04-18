import time

max_level = 4
blacklist = []
callback = None

def dbg(text, module, level=1):
    """
    show the debug on the console
    """
    if level <= max_level and module not in blacklist:
        output = "[%s %s] %s" % (time.strftime('%H:%M:%S'), module, text)
        if callback is None:
            print output
        else:
            callback(text, module, level, output)

