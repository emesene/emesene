#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import os
import sys
import re
import zipfile
import shutil

TARGET_DIR = "C://emesene//bundle"
URL_BUNDLE = "http://optionexplicit.be/projects/gnome-windows/GTK+3/gtk+/git/"
#FIXME: move to git repo
PATCHED_FILE = "http://ubuntuone.com/0rnj0GhbbYN3pI0dtOQazm"

def main():
    ensure_bundle()


def ensure_bundle(force=False):
    print "searching for gtk bundle"
    bundle_dir = os.path.join(get_current_dir(), TARGET_DIR)

    if not has_cached_bundle(bundle_dir):
        print "gtk bundle not found. Starting download"
        f = urllib.urlopen(URL_BUNDLE)
        s = f.read()
        f.close()
        url_re = re.compile("(gtk\+-bundle-.*-win32.zip)\"")
        m = url_re.search(s)
        full_url = URL_BUNDLE + m.group(1)
        #FIXME: implement download
        download_bundle(full_url)
    else:
        print "cached gtk bundle found"

    name = get_bundle_name(bundle_dir)
    print "extracting gtk bundle files"
    sourceZip = zipfile.ZipFile(os.path.join(bundle_dir, name), 'r')
    for f in sourceZip.namelist():
        #avoid unneeded content
        if (not f.endswith('/')
            and not f.startswith('include')
            and not f.startswith('man')
            and not f.startswith('manifest')
            and not f.startswith('src')
            and not f.startswith('lib/gdbus-2.0')
            and not f.startswith('lib/gettext')
            and not f.startswith('lib/pkgconfig')
            and not f.startswith('lib/glib-2.0/include')
            and not f.startswith('lib/gobject-introspection')
            and not f.startswith('share/doc')
            and not f.startswith('share/info')
            and not f.startswith('share/icons')
            and not f.startswith('share/emacs')
            and not f.startswith('share/gdb')
            and not f.startswith('share/glib-2.0/gdb')
            and not f.startswith('share/man')
            and not f.startswith('share/bash-completion')
            and not f.startswith('share/gobject-introspection-1.0')
            and not f.startswith('share/gtk-3.0/demo')
            and not f.startswith('share/gtk-doc')
            and not f.startswith('share/glib-2.0/gettext')
            and not f.startswith('share/gettext')
            and not f.startswith('share/aclocal')
            and not f.startswith('share/themes/Emacs')
            and not f.startswith('Lib/pkgconfig')
            and not f.endswith('.la')
            and not f.endswith('.exe')
            and not f.endswith('.def')):
                #skip non .dll files
                if f.startswith('bin/') and not f.endswith('.dll'):
                    continue
                if f.startswith('Lib/'):
                    dest = os.path.join(bundle_dir, 'lib2')
                else:
                    dest = bundle_dir
                sourceZip.extract(f, dest)

    sourceZip.close()
    reorder_bundle_tree(bundle_dir)


def reorder_bundle_tree(bundle_dir):
    #create new gtk3 folder
    print "reordering tree. this will take some time"
    gtk_dir = os.path.join(bundle_dir, "lib2/Lib/site-packages/gtk3")
    try:
        shutil.rmtree(gtk_dir)
    except:
        pass
    os.mkdir(gtk_dir)

    shutil.move(os.path.join(bundle_dir, "lib2/Lib/libpyglib-gi-2.0-python.dll.a"),
        os.path.join(bundle_dir, "lib2/Lib/site-packages/libpyglib-gi-2.0-python.dll.a"))


    shutil.move(os.path.join(bundle_dir, "etc"), os.path.join(gtk_dir, "etc"))
    shutil.move(os.path.join(bundle_dir, "share"), os.path.join(gtk_dir, "share"))
    shutil.move(os.path.join(bundle_dir, "lib"), os.path.join(gtk_dir, "lib"))
    shutil.move(os.path.join(bundle_dir, "bin"), os.path.join(gtk_dir, "bin"))

    print "patching tree"
    # create pth file
    inp = file(os.path.join(bundle_dir, "lib2/Lib/site-packages/pygi.pth"), 'w')
    inp.write("import distutils.sysconfig, os; os.putenv('PATH', os.path.join(distutils.sysconfig.get_python_lib(),'gtk3/bin;') + os.getenv('PATH'))")
    inp.close()

    #download pached pygtkcompat file
    f = urllib.urlopen(PATCHED_FILE)
    dest_url = os.path.join(bundle_dir, "lib2/Lib/site-packages/gi/pygtkcompat.py")
    dest = file(dest_url, 'w')
    dest.write(f.read())
    dest.close()
    f.close()

    dest_dir = get_python_dir()
    print "bundle will be copied into %s" % dest_dir
    #FIXME: activate this copy into python folder
#    copy_replace(os.path.join(bundle_dir, "lib2//Lib/site-packages"), dest_dir)
    print "you can now use gtk3 on your python instalation"


def silent_remove(path):
    try:
        shutil.rmtree(path)
    except:
        pass


#http://stackoverflow.com/questions/7419665/python-move-and-overwrite-files-and-folders
def copy_replace(root_src_dir, root_dst_dir):
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir)
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)


def download_bundle(url):
    print "download bundle from %s" % url
    raise RuntimeError


def has_cached_bundle(bundle_dir):
    '''return true if bundle has to be downloaded'''
    if not os.path.exists(bundle_dir):
        return False
    if get_bundle_name(bundle_dir) is not None:
        return True
    return False


def get_bundle_name(bundle_dir):
    '''return the bundle name'''
    for dirname, dirnames, files in os.walk(bundle_dir):
        for f in files:
            if f.startswith("gtk+-bundle-"):
                return f
    return None


def get_current_dir():
    '''get current path'''
    this_module_path = os.path.dirname(unicode(__file__,
        sys.getfilesystemencoding()))
    return os.path.abspath(this_module_path)


def get_python_dir():
    # gtk sources will be in a path like this:
    #"C:\\Python27\\Lib\\site-packages\\gtk3"
    for p in sys.path:
        if p.endswith("site-packages"):
            return p
    return None

if __name__ == "__main__":
    main()
