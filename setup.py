#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

import os
import platform
import sys

python_version = platform.python_version()[0:3]

setup_info = dict(
    name = "emesene",
    version = "2.12.1",
    description = "Instant Messaging Client",
    author = "Luis Mariano Guerra",
    author_email = "luismarianoguerra@gmail.com",
    keywords = "messenger im msn jabber gtalk live facebook",
    long_description = """emesene is an istant messenger capable of connecting
    to various networks and utilizing different graphical toolkits.
    Currently msn and jabber are supported through papyon and xmppy,
    which allows emesene to connect to various IM services such as
    Windows Live Messenger, GTalk, Facebook Chat, etc.""",
    url = "http://www.emesene.org/",
    license = "GNU GPL 3",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Communications :: Chat",
    ],
    ext_package = "emesene",
    include_package_data = True,
    package_data = {
        "emesene": [
            "themes/conversations/*/*/*/*/*",
            "themes/emotes/*/*",
            "themes/images/*/*/*",
            "themes/sounds/*/*"
        ]
    }
)


def windows_check():
    return platform.system() in ("Windows", "Microsoft")

def osx_check():
    return platform.system() == "Darwin"


if os.name == "nt":
    import py2exe

    _data_files = [("data",["emesene/data/hotmlog.htm"])]

    #include data files, like images, xml, html files
    for dir in ['emesene/e3', 'emesene/gui', 'emesene/po', 'emesene/themes']:
        for dirname, dirnames, files in os.walk(dir):
            if dirname.find("xmppy") == -1 and dirname.find("papylib\papyon") == -1:
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
                    _data_files.append((dirname[8:], fpath))

    #include all needed dlls
    for dirname, dirnames, files in os.walk("dlls"):
        fpath = []
        for f in files:
            fpath.append(os.path.join(dirname, f))
        if fpath != []:
            _data_files.append((".", fpath))

    #include gtk runtime/share, runtime/lib and runtime/etc
    for path in sys.path:
        if path.find("gtk") != -1:
            for dirname, dirnames, files in os.walk(path+"\\runtime\\share\\"):
                dir = dirname.replace(path+"\\runtime\\share\\","")
                to = dirname.replace(path+"\\runtime\\","")
                #ignore unneded folders
                if dir.startswith('glib-2.0') or \
                   dir.startswith('gtk-2.0') or \
                   dir.startswith('icons') or \
                   dir.startswith('locale') or \
                   dir.startswith('themes') or \
                   dir.startswith('webkit-1.0') or \
                   dir.startswith('xml'):
                    #ignore extra themes
                    if not dir.startswith("themes\\Default\\") and \
                       not dir.startswith("themes\\Emacs\\") and \
                       not dir.startswith("themes\\Raleigh\\"):
                        fpath = []
                        for f in files:
                            fpath.append(os.path.join(dirname, f))
                        if fpath != []:
                            _data_files.append((to, fpath))
            for dirname, dirnames, files in os.walk(path+"\\runtime\\lib\\"):
                to = dirname.replace(path+"\\runtime\\","")
                fpath = []
                for f in files:
                    #ignore some files
                    if not f.endswith(".a") and not f.endswith(".lib"):
                        fpath.append(os.path.join(dirname, f))
                if fpath != []:
                    _data_files.append((to, fpath))
            for dirname, dirnames, files in os.walk(path+"\\runtime\\etc\\"):
                to = dirname.replace(path+"\\runtime\\","")
                fpath = []
                for f in files:
                    fpath.append(os.path.join(dirname, f))
                if fpath != []:
                    _data_files.append((to, fpath))
    #Use clearlooks theme
    for dirname, dirnames, files in os.walk(".\\windows\\Clearlooks\\"):
        to = dirname.replace(".\\windows\\Clearlooks\\","")
        fpath = []
        for f in files:
            fpath.append(os.path.join(dirname, f))
        if fpath != []:
            _data_files.append((to, fpath))

    # include all needed modules
    includes = ["locale", "gio", "cairo", "pangocairo", "pango",
                "atk", "gobject", "os", "code", "winsound", "win32api",
                "plistlib", "win32gui", "OpenSSL", "Crypto", "Queue", "sqlite3",
                "glob", "webbrowser", "json", "imaplib", "cgi", "gzip", "uuid",
                "platform", "imghdr", "ctypes", "optparse", "plugin_base",
                "e3.msn", "papyon", "xmpp", "plugins","webkit"]

    # incude gui.common modules manually, i guess py2exe doesn't do that
    # automatically because the imports are made inside some functions    
    for dirname, dirnames, files in os.walk("emesene\\gui\\common"):
        fpath = []
        for f in files:
            if f != "__init__.py" and f.endswith(".py"):
                includes.append("gui.common."+f[:-2])

    opts = {
        "py2exe": {
            "packages": ["encodings", "gtk", "OpenSSL", "Crypto", "xml",
                         "xml.etree", "xml.etree.ElementTree"],
            "includes": includes,
            "excludes": ["ltihooks", "pywin", "pywin.debugger",
                "pywin.debugger.dbgcon", "pywin.dialogs",
                "pywin.dialogs.list", "Tkconstants", "Tkinter", "tcl",
                "doctest", "macpath", "pdb", "cookielib", "ftplib",
                "pickle", "win32wnet", "unicodedata",
                "getopt", "gdk"],
            "dll_excludes": ["libglade-2.0-0.dll", "w9xpopen.exe"],
            "optimize": "2",
            "dist_dir": "dist",
            "skip_archive": 1
        }
    }

    # Add paths so we don't need to copy files to ./emesene and we can run the
    # setup from outside emesene's source folder
    sys.path.insert(0, os.path.abspath("./dlls"))
    sys.path.insert(0, os.path.abspath("./emesene"))
    sys.path.insert(0, os.path.abspath("./emesene/e3/papylib/papyon"))
    sys.path.insert(0, os.path.abspath("./emesene/e3/jabber/xmppy"))

    # run setup
    setup(
       requires   = ["gtk"],
       windows    = [{"script": "emesene/emesene.py", "icon_resources": [(1, "emesene.ico")], "dest_base": "emesene"},
                     {"script": "emesene/emesene.py", "icon_resources": [(1, "emesene.ico")], "dest_base": "emesene_portable"}],
       console    = [{"script": "emesene/emesene.py", "icon_resources": [(1, "emesene.ico")], "dest_base": "emesene_debug"},
                     {"script": "emesene/emesene.py", "icon_resources": [(1, "emesene.ico")], "dest_base": "emesene_portable_debug"}],
       options    = opts,
       data_files = _data_files,
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

    setup(data_files = _data_files,
        packages = find_packages(), **setup_info)
