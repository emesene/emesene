

"""this module was based on setup.py from pygame-ctype branch.
author: Alex Holkner <aholkner@cs.rmit.edu.au>"""

import os
from os.path import join, abspath, dirname, splitext
import sys
import subprocess

from distutils.cmd import Command


# A "do-everything" command class for building any type of documentation.
class BuildDocCommand(Command):
    user_options = [('doc-dir=', None, 'directory to build documentation'),
                    ('epydoc=', None, 'epydoc executable')]

    def initialize_options(self):
        self.doc_dir = join(abspath(dirname(sys.argv[0])), 'doc')
        self.epydoc = 'epydoc'

    def finalize_options(self):
        pass

    def run(self):
        if 'pre' in self.doc:
            subprocess.call(self.doc['pre'], shell=True)

        prev_dir = os.getcwd()
        if 'chdir' in self.doc:
            dir = abspath(join(self.doc_dir, self.doc['chdir']))
            try:
                os.makedirs(dir)
            except:
                pass
            os.chdir(dir)

        if 'config' in self.doc:
            cmd = [self.epydoc,
                   '--no-private',
                   '--no-frames',
                   '--config "%s"' % self.doc['config']]
            subprocess.call(' '.join(cmd), shell=True)

        os.chdir(prev_dir)
        
        if 'post' in self.doc:
            subprocess.call(self.doc['post'], shell=True)

# Fudge a command class given a dictionary description
def make_doc_command(**kwargs):
    class c(BuildDocCommand):
        doc = dict(**kwargs)
        description = 'build %s' % doc['description']
    c.__name__ = 'build_doc_%s' % c.doc['name'].replace('-', '_')
    return c

# This command does nothing but run all the other doc commands.
# (sub_commands are set later)
class BuildAllDocCommand(Command):
    description = 'build all documentation'
    user_options = []
    sub_commands = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

