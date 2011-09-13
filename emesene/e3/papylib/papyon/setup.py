from distutils.core import setup
from doc import make_doc_command, BuildAllDocCommand
import os

import papyon


# Metadata
NAME = "papyon"
VERSION = papyon.__version__
DESCRIPTION = "Python msn client library"
AUTHOR = "Youness Alaoui"
AUTHOR_EMAIL = "kakaroto@users.sourceforge.net"
URL = papyon.__url__
LICENSE = papyon.__license__

# Documentation
doc_commands = {
    'doc_user_api': make_doc_command(
        name='user_api',
        description='the papyon user API documentation',
        config='doc/user-api.conf'),
    'doc': BuildAllDocCommand
}
for name in doc_commands.keys():
    if name != 'doc':
        BuildAllDocCommand.sub_commands.append((name, None))

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
def path_split(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return path_split(head, [tail] + result)

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
pieces = path_split(root_dir)
if pieces[-1] == '':
    len_root_dir = len(pieces) - 1
else:
    len_root_dir = len(pieces)

for directory in ('papyon',):
    papyon_dir = os.path.join(root_dir, directory)
    for dirpath, dirnames, filenames in os.walk(papyon_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'):
                del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(path_split(dirpath)[len_root_dir:]))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# Setup
setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      license=LICENSE,
      platforms=["any"],
      packages=packages,
      cmdclass=doc_commands,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Telecommunications Industry',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: POSIX',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python',
          'Topic :: Communications :: Chat',
          'Topic :: Communications :: Telephony',
          'Topic :: Internet',
          'Topic :: Software Development :: Libraries :: Python Modules'
          ])
