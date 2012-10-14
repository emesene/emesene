#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

import os
import sys
import shutil

import emesene.Info

setup_info = dict(
    name="emesene",
    version=emesene.Info.EMESENE_VERSION,
    description="Instant Messaging Client",
    author=emesene.Info.EMESENE_AUTHORS,
    author_email="luismarianoguerra@gmail.com",
    keywords="messenger im msn jabber gtalk live facebook",
    long_description="""emesene is an istant messenger capable of connecting
    to various networks and utilizing different graphical toolkits.
    Currently msn and jabber are supported through papyon and SleekXMPP,
    which allows emesene to connect to various IM services such as
    Windows Live Messenger, GTalk, Facebook Chat, etc.""",
    url=emesene.Info.EMESENE_WEBSITE,
    license="GNU GPL 3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: Chat",
    ],
    ext_package="emesene",
    include_package_data=True,
    package_data={
        "emesene": [
            "themes/conversations/*/*/*/*/*",
            "themes/emotes/*/*",
            "themes/images/*/*/*",
            "themes/sounds/*/*"
        ]
    }
)

if os.name == "nt":
    import py2exe

    _data_files = []

    # get current path
    this_module_path = os.path.dirname(unicode(__file__,
        sys.getfilesystemencoding()))

    current_path = os.path.abspath(this_module_path)
    source_path = os.path.join(current_path, 'emesene')
    dist_path = os.path.join(current_path, "dist")

    # gtk sources will be in a path like this:
    #"C:\\Python27\\Lib\\site-packages\\gtk3"
    package_path = ""
    for p in sys.path:
        if p.endswith("site-packages"):
            package_path = p
            break
    gtk3_path = package_path + "\\gtk3"

    # include dll files
    for dirname, dirnames, files in os.walk(os.path.join(gtk3_path, '/bin')):
        fpath = []
        for f in files:
            if f.endswith(".dll"):
                fpath.append(os.path.join(dirname, f))
        if fpath != []:
            _data_files.append((".", fpath))

    #calculate padding needed to make relative paths
    padding = len(source_path) + 1
    #include data files, like images, xml, html files
    for dir in ['e3', 'gui', 'po', 'themes']:
        for dirname, dirnames, files in os.walk(os.path.join(source_path, dir)):
            if dirname.find("SleekXMPP") == -1 and \
                dirname.find("papylib\papyon") == -1:
                fpath = []
                for f in files:
                #ignore pyc, py, .gitignore, .doxygen and lintreport.sh files
                    if not f.endswith(".pyc") \
                      and not f.endswith(".py") \
                      and not f.startswith(".git") \
                      and not f == ".doxygen" \
                      and not f == "lintreport.sh":
                        fpath.append(os.path.join(dirname, f))
                if fpath != []:
                    # use relative path as key
                    _data_files.append((dirname[padding:], fpath))

    #include gtk share, lib and etc
    for dirname, dirnames, files in os.walk(gtk3_path + "\\share\\"):
        to = dirname.replace(gtk3_path + "\\", "")
        fpath = []
        for f in files:
            fpath.append(os.path.join(dirname, f))
        if fpath != []:
            _data_files.append((to, fpath))

    for dirname, dirnames, files in os.walk(gtk3_path + "\\lib\\"):
        to = dirname.replace(gtk3_path + "\\", "")
        fpath = []
        for f in files:
			#ignore some files
			if not f.endswith(".a") and not f.endswith(".lib"):
				fpath.append(os.path.join(dirname, f))
        if fpath != []:
            _data_files.append((to, fpath))

    for dirname, dirnames, files in os.walk(gtk3_path + "\\etc\\"):
        to = dirname.replace(gtk3_path + "\\", "")
        fpath = []
        for f in files:
			fpath.append(os.path.join(dirname, f))
        if fpath != []:
			_data_files.append((to, fpath))

    # include all needed modules
    includes = ["locale", "os", "code", "winsound", "win32api",
                "plistlib", "win32gui", "OpenSSL", "Crypto", "Queue", "sqlite3",
                "glob", "webbrowser", "json", "imaplib", "cgi", "gzip", "uuid",
                "platform", "imghdr", "ctypes", "optparse", "plugin_base",
                "pyfb", "papyon", "e3.xmpp", "unicodedata", 'sleekxmpp']#, "dnspython"]

    # include gui.common modules manually, i guess py2exe doesn't do that
    # automatically because the imports are made inside some functions
    for dirname, dirnames, files in os.walk(os.path.join(source_path, "gui\\common")):
        fpath = []
        for f in files:
            if f != "__init__.py" and f.endswith(".py"):
                includes.append("gui.common." + f[:-2])

    #replace sleekxmpp dir as py2exe doesn't copy all the needed files
    features_dir = os.path.join(dist_path, "sleekxmpp")
    source_features_dir = os.path.join(source_path, "e3\\xmpp\\SleekXMPP\\sleekxmpp")
    try:
        shutil.rmtree(features_dir)
    except:
        pass
    shutil.copytree(source_features_dir,
                    features_dir,
                    ignore=shutil.ignore_patterns(('*.pyc')))

    ##replace autogenerated gi dir because some files are missing by py2exe
    features_dir = os.path.join(dist_path, "gi")
    source_features_dir = os.path.join(package_path, "gi")
    try:
        shutil.rmtree(features_dir)
    except:
        pass

    shutil.copytree(source_features_dir,
                    features_dir,
                    ignore=shutil.ignore_patterns(('*.pyc')))

    ##replace autogenerated cairo dir because some files are missing by py2exe
    features_dir = os.path.join(dist_path, "cairo")
    source_features_dir = os.path.join(package_path, "cairo")
    try:
        shutil.rmtree(features_dir)
    except:
        pass
    shutil.copytree(source_features_dir,
                    features_dir,
                    ignore=shutil.ignore_patterns(('*.pyc')))

	###
    root_src_dir = os.path.join(package_path, "gtk3//bin")
    root_dst_dir = dist_path
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.copy(src_file, dst_dir)
					
    opts = {
        "py2exe": {
            "packages": ["encodings", "OpenSSL", "Crypto", "xml",
                         "xml.etree", "xml.etree.ElementTree"],
            "includes": includes,
            "excludes": ["ltihooks", "pywin", "pywin.debugger",
                "pywin.debugger.dbgcon", "pywin.dialogs",
                "pywin.dialogs.list", "Tkconstants", "Tkinter", "tcl",
                "doctest", "macpath", "pdb", "cookielib", "ftplib",
                "pickle", "win32wnet",
                "getopt"],
            "dll_excludes": ["w9xpopen.exe"],
            "optimize": "2",
            "dist_dir": dist_path,
            "skip_archive": 1
        }
    }

    # Add paths so we don't need to copy files to ./emesene and we can run the
    # setup from outside emesene's source folder
    sys.path.insert(0, dist_path)
    sys.path.insert(0, gtk3_path + '//bin')
    sys.path.insert(0, os.path.join(current_path, 'emesene'))
    sys.path.insert(0, os.path.join(current_path, 'emesene/plugins'))
    sys.path.insert(0, os.path.join(current_path, 'emesene/e3/papylib/papyon'))
    sys.path.insert(0, os.path.join(current_path, 'emesene/e3/xmpp/SleekXMPP'))
    sys.path.insert(0, os.path.join(current_path, 'emesene/e3/xmpp/pyfb'))

    ico_path = os.path.join(current_path, 'emesene.ico')
    script_path = os.path.join(current_path, 'emesene/emesene.py')
    # run setup
    setup(
       requires=[],
       windows=[{"script": script_path,"icon_resources": [(1, ico_path)], "dest_base": "emesene"},
                     {"script": script_path, "icon_resources": [(1, ico_path)], "dest_base": "emesene_portable"}],
       console=[{"script": script_path, "icon_resources": [(1, ico_path)], "dest_base": "emesene_debug"},
                     {"script": script_path, "icon_resources": [(1, ico_path)], "dest_base": "emesene_portable_debug"}],
       options=opts,
       data_files=_data_files,
       **setup_info
    )
    print "done! files at: dist"

else:
    # Data files to be installed to the system
    _data_files = [
        ("share/icons/hicolor/scalable/apps", ["emesene/data/icons/hicolor/scalable/apps/emesene.svg"]),
        ("share/icons/hicolor/16x16/apps", ["emesene/data/icons/hicolor/16x16/apps/emesene.png"]),
        ("share/icons/hicolor/22x22/apps", ["emesene/data/icons/hicolor/22x22/apps/emesene.png"]),
        ("share/icons/hicolor/24x24/apps", ["emesene/data/icons/hicolor/24x24/apps/emesene.png"]),
        ("share/icons/hicolor/32x32/apps", ["emesene/data/icons/hicolor/32x32/apps/emesene.png"]),
        ("share/icons/hicolor/36x36/apps", ["emesene/data/icons/hicolor/36x36/apps/emesene.png"]),
        ("share/icons/hicolor/48x48/apps", ["emesene/data/icons/hicolor/48x48/apps/emesene.png"]),
        ("share/icons/hicolor/64x64/apps", ["emesene/data/icons/hicolor/64x64/apps/emesene.png"]),
        ("share/icons/hicolor/72x72/apps", ["emesene/data/icons/hicolor/72x72/apps/emesene.png"]),
        ("share/icons/hicolor/96x96/apps", ["emesene/data/icons/hicolor/96x96/apps/emesene.png"]),
        ("share/icons/hicolor/128x128/apps", ["emesene/data/icons/hicolor/128x128/apps/emesene.png"]),
        ("share/icons/hicolor/192x192/apps", ["emesene/data/icons/hicolor/192x192/apps/emesene.png"]),
        ("share/icons/hicolor/256x256/apps", ["emesene/data/icons/hicolor/256x256/apps/emesene.png"]),
        ("share/applications", ["emesene/data/share/applications/emesene.desktop"]),
        ("share/pixmaps", ["emesene/data/pixmaps/emesene.png", "emesene/data/pixmaps/emesene.xpm"]),
        ("share/man/man1", ["docs/man/emesene.1"])
    ]

    setup(data_files=_data_files, packages=find_packages(), **setup_info)
