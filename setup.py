#!/usr/bin/python

from distutils.core import setup, Extension

# Data files to be installed to the system
_data_files = [
    ('share/icons/scalable/apps', ['emesene/data/icons/scalable/apps/emesene.svg']),
    ('share/icons/hicolor/128x128/apps', ['emesene/data/icons/hicolor/128x128/apps/emesene.png']),
    ('share/icons/hicolor/16x16/apps', ['emesene/data/icons/hicolor/16x16/apps/emesene.png']),
    ('share/icons/hicolor/192x192/apps', ['emesene/data/icons/hicolor/192x192/apps/emesene.png']),
    ('share/icons/hicolor/22x22/apps', ['emesene/data/icons/hicolor/22x22/apps/emesene.png']),
    ('share/icons/hicolor/24x24/apps', ['emesene/data/icons/hicolor/24x24/apps/emesene.png']),
    ('share/icons/hicolor/256x256/apps', ['emesene/data/icons/hicolor/256x256/apps/emesene.png']),
    ('share/icons/hicolor/32x32/apps', ['emesene/data/icons/hicolor/32x32/apps/emesene.png']),
    ('share/icons/hicolor/36x36/apps', ['emesene/data/icons/hicolor/36x36/apps/emesene.png']),
    ('share/icons/hicolor/48x48/apps', ['emesene/data/icons/hicolor/48x48/apps/emesene.png']),
    ('share/icons/hicolor/64x64/apps', ['emesene/data/icons/hicolor/64x64/apps/emesene.png']),
    ('share/icons/hicolor/72x72/apps', ['emesene/data/icons/hicolor/72x72/apps/emesene.png']),
    ('share/icons/hicolor/96x96/apps', ['emesene/data/icons/hicolor/96x96/apps/emesene.png']),
    ('share/applications', ['emesene/data/share/applications/emesene.desktop']),
    ('share/pixmaps', ['emesene/data/pixmaps/emesene.png', 'emesene/data/pixmaps/emesene.xpm']),
    ('share/man/man1', ['docs/man/emesene.1'])
]

setup(
    name = 'emesene',
    version = '2.0',
    description = 'MSN messenger client',
    author = 'Luis Mariano Guerra',
    author_email = 'luismarianoguerra@gmail.com',
    url = 'http://www.emesene.org/',
    license = 'GNU GPL 3',
    
    requires = ['gtk', 'papyon'],
    platforms = ['any'],
    data_files = _data_files,
    ext_package = "emesene",
    ext_modules = _ext_modules,
    include_package_data = True,
    package_data = { "emesene" : [ ]},
    packages = find_packages(exclude=["plugins", "docs", "tests"]),

    ['', 'e3', 'e3.base', 'e3.cache', 'e3.common',
			   'e3.dummy', 'e3.jabber', 'e3.jabber.xmpp', 'e3.msn',
			   'e3.msn.msgs', 'e3.msn.p2p', 'e3.papylib', 'gui',
			   'gui.base', 'gui.gtkui', 'interfaces', 'plugins.music',
			   'plugins.music.thirdparty', 'plugins.ye_old_status_combo'],
          scripts      = ['emesene'],
          package_data = {'': ['docs/*', 'e3/msn/xml templates/*',
                               'e3/papylib/papyon', 'test/*', 'themes/*/*',
                               'plugins/link.py', 'plugins/plugin.pylint.rc', 'test/test_all.sh'],
                          'gui.base': ['template.html'],
                          'gui.gtkui': ['conversation.html'],
                          'plugins.music.thirdparty': ['README.txt']},
          data_files   = [('share/pixmaps', ['emesene-logo.png']),               
                          ('share/applications', ['emesene.desktop'])]          
          )
