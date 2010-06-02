#!/usr/bin/python

from distutils.core import setup, Extension

setup(    name         = 'emesene',
          version      = '2.0',
          description  = 'MSN messenger client',
          author       = 'Luis Mariano Guerra, dx, C10uD',
          author_email = 'luismarianoguerra@gmail.com',
          url          = 'http://www.emesene.org/',
          license      = 'GNU GPL 3',
          requires     = ['gtk', 'papyon'],
          platforms    = ['any'],
          packages     = ['', 'e3', 'e3.base', 'e3.cache', 'e3.common',
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
