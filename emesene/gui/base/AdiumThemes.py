'''a module to handle themes'''
import os
import glob

import AdiumTheme

DIRECTORY, FILE = range(2)

REQUIRED_FILES = [
        {'name': 'Contents', 'type': DIRECTORY, 'childs': [
            {'name': 'Info.plist', 'type': FILE},
            {'name': 'Resources', 'type': DIRECTORY, 'childs': [
                #{'name': 'main.css', 'type': FILE},
                {'name': 'Status.html', 'type': FILE},
                {'name': 'Incoming', 'type': DIRECTORY, 'childs': [
                    {'name': 'Content.html', 'type': FILE},
                ]}
            ]}
        ]}]

__instance = None

def get_instance():
    '''singleton for Themes class
    '''
    global __instance

    if __instance is None:
        __instance = AdiumThemes()

    return __instance


class AdiumThemes(object):
    '''a class to handle adium themes
    '''

    def __init__(self):
        '''constructor'''

        # the paths to look for themes
        self.paths = []

    def add_themes_path(self, path):
        '''add a path to look for themes

        returns True if the path was added, False otherwise (the path doesn't
        exists or it isn't a directory)
        '''

        if path not in self.paths and os.path.isdir(path):
            self.paths.append(path)
            return True

        return False

    def list(self):
        '''return a list of all the available themes
        '''
        items = []

        for path in self.paths:
            items += glob.glob(os.path.join(path, "*.AdiumMessageStyle"))

        return items

    def get(self, theme_path, timefmt="%H:%M"):
        '''return a Theme object instance
        returs True, theme_instance if the validation was ok
        False, reason if some validation failed
        '''
        status, message = self.validate(theme_path)

        if not status:
            return status, message

        return True, AdiumTheme.AdiumTheme(theme_path, timefmt)

    def validate(self, theme_path):
        '''validate a Theme directory structure
        '''

        if not os.path.isdir(theme_path):
            return False, "%s is not a directoy" % (theme_path,)

        return self.validate_structure(theme_path, REQUIRED_FILES)

    def validate_structure(self, base_path, structure):
        '''validate the required files and directories from base_path
        '''

        for item in structure:
            name = os.path.join(base_path, item['name'])

            if item['type'] == FILE:
                if not os.path.isfile(name):
                    return False, "%s is not a file" % (name, )
                if not os.access(name, os.R_OK):
                    return False, "%s is not readable" % (name, )
            elif item['type'] == DIRECTORY:
                if not os.path.isdir(name):
                    return False, "%s is not a directory" % (name, )

                return self.validate_structure(name, item['childs'])

        return True, "ok"

