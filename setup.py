#!/usr/bin/python

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages, Extension

import os
import platform

python_version = platform.python_version()[0:3]

def windows_check():
    return platform.system() in ('Windows', 'Microsoft')

def osx_check():
    return platform.system() == "Darwin"

# Data files to be installed to the system
_data_files = [
    ('share/icons/scalable/apps', ['emesene/data/icons/scalable/apps/emesene.svg']),
    ('share/icons/hicolor/16x16/apps', ['emesene/data/icons/hicolor/16x16/apps/emesene.png']),
    ('share/icons/hicolor/22x22/apps', ['emesene/data/icons/hicolor/22x22/apps/emesene.png']),
    ('share/icons/hicolor/24x24/apps', ['emesene/data/icons/hicolor/24x24/apps/emesene.png']),
    ('share/icons/hicolor/32x32/apps', ['emesene/data/icons/hicolor/32x32/apps/emesene.png']),
    ('share/icons/hicolor/36x36/apps', ['emesene/data/icons/hicolor/36x36/apps/emesene.png']),
    ('share/icons/hicolor/48x48/apps', ['emesene/data/icons/hicolor/48x48/apps/emesene.png']),
    ('share/icons/hicolor/64x64/apps', ['emesene/data/icons/hicolor/64x64/apps/emesene.png']),
    ('share/icons/hicolor/72x72/apps', ['emesene/data/icons/hicolor/72x72/apps/emesene.png']),
    ('share/icons/hicolor/96x96/apps', ['emesene/data/icons/hicolor/96x96/apps/emesene.png']),
    ('share/icons/hicolor/128x128/apps', ['emesene/data/icons/hicolor/128x128/apps/emesene.png']),
    ('share/icons/hicolor/192x192/apps', ['emesene/data/icons/hicolor/192x192/apps/emesene.png']),
    ('share/icons/hicolor/256x256/apps', ['emesene/data/icons/hicolor/256x256/apps/emesene.png']),
    ('share/applications', ['emesene/data/share/applications/emesene.desktop']),
    ('share/pixmaps', ['emesene/data/pixmaps/emesene.png', 'emesene/data/pixmaps/emesene.xpm']),
    ('share/man/man1', ['docs/man/emesene.1'])
]

setup(

    name = 'emesene',
    version = '1.9.0',
    description = 'Instant Messaging Client',
    author = 'Luis Mariano Guerra',
    author_email = 'luismarianoguerra@gmail.com',
    keywords = "messenger im msn jabber gtalk live facebook",
    long_description = """emesene is an istant messenger capable of connecting
        to various networks and utilizing different graphical toolkits.
        Currently msn and jabber are supported through papyon and xmppy,
        which allows emesene to connect to various IM services such as
        Windows Live Messenger, GTalk, Facebook Chat, etc.""",
    url = 'http://www.emesene.org/',
    license = 'GNU GPL 3',

    data_files = _data_files,
    ext_package = "emesene",
    include_package_data = True,
    package_data = {"emesene" : ['themes/conversations/*/*/*/*/*', 
                                 'themes/emotes/*/*',
                                 'themes/images/*/*',
                                 'themes/sounds/*/*']},
    packages = find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: Chat",
    ],
     )
