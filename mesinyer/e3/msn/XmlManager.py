'''handle the requests to get the xml templates'''

import os
import common

TEMPLATE_FOLDER = os.path.abspath(os.path.dirname(__file__)) + '/xml templates'

def get(name, *args):
    '''try to get a template from the template folder and return it,
    return None if not found'''

    name = os.path.join(TEMPLATE_FOLDER, name + '.xml')
    if os.access(name, os.R_OK):
        xml = file(name, 'r')
        template = xml.read()
        xml.close()
        return template % tuple([common.escape(x) for x in args])

    return None


