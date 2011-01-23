'''Get enchant dicts'''
# Code tooked from pyenchant
#
# Copyright (C) 2004-2008, Ryan Kelly
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPsE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#
# In addition, as a special exception, you are
# given permission to link the code of this program with
# non-LGPL Spelling Provider libraries (eg: a MSFT Office
# spell checker backend) and distribute linked combinations including
# the two.  You must obey the GNU Lesser General Public License in all
# respects for all of the code used other than said providers.  If you modify
# this file, you may extend this exception to your version of the
# file, but you are not obligated to do so.  If you do not wish to
# do so, delete this exception statement from your version.
#

import sys, os, os.path
from ctypes import *
from ctypes.util import find_library

# Locate and load the enchant dll.
# We've got several options based on the host platform.

class Error(Exception):
    """Base exception class for the enchant module."""
    pass

def get_resource_filename(resname):
    """Get the absolute path to the named resource file.

    This serves widely the same purpose as pkg_resources.resource_filename(),
    but tries to avoid loading pkg_resources unless we're actually in
    an egg.
    """
    path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(path,resname)
    if os.path.exists(path):
        return path
    if hasattr(sys, "frozen"):
        exe_path = unicode(sys.executable,sys.getfilesystemencoding())
        exe_dir = os.path.dirname(exe_path)
        path = os.path.join(exe_dir, resname)
        if os.path.exists(path):
            return path
    else:
        import pkg_resources
        try:
            path = pkg_resources.resource_filename("enchant",resname)
        except KeyError:
            pass
        else:
            path = os.path.abspath(path)
            if os.path.exists(path):
                return path
    raise Error("Could not locate resource '%s'" % (resname,))

e = None

def _e_path_possibilities():
    """Generator yielding possible locations of the enchant library."""
    yield os.environ.get("PYENCHANT_LIBRARY_PATH")
    yield find_library("enchant")
    yield find_library("libenchant")
    yield find_library("libenchant-1")
    if sys.platform == 'darwin':
         # enchant lib installed by macports
         yield "/opt/local/lib/libenchant.dylib"


# On win32 we ship a bundled version of the enchant DLLs.
# Use them if they're present.
if sys.platform == "win32":
    e_path = None
    try:
        e_path = get_resource_filename("libenchant.dll")
    except (Error,ImportError):
         try:
            e_path = get_resource_filename("libenchant-1.dll")
         except (Error,ImportError):
            pass
    if e_path is not None:
        # We need to use LoadLibraryEx with LOAD_WITH_ALTERED_SEARCH_PATH so
        # that we don't accidentally suck in other versions of e.g. glib.
        if not isinstance(e_path,unicode):
            e_path = unicode(e_path,sys.getfilesystemencoding())
        LoadLibraryEx = windll.kernel32.LoadLibraryExW
        LOAD_WITH_ALTERED_SEARCH_PATH = 0x00000008
        e_handle = LoadLibraryEx(e_path,None,LOAD_WITH_ALTERED_SEARCH_PATH)
        if not e_handle:
            raise WinError()
        e = CDLL(e_path,handle=e_handle)


# On darwin we ship a bundled version of the enchant DLLs.
# Use them if they're present.
if e is None and sys.platform == "darwin":
  try:
      e_path = get_resource_filename("lib/libenchant.1.dylib")
  except (Error,ImportError):
      pass
  else:
      # Enchant doesn't natively support relocatable binaries on OSX.
      # We fake it by patching the enchant source to expose a char**, which
      # we can write the runtime path into ourelves.
      e = CDLL(e_path)
      try:
          e_dir = os.path.dirname(os.path.dirname(e_path))
          prefix_dir = POINTER(c_char_p).in_dll(e,"enchant_prefix_dir_p")
          prefix_dir.contents = c_char_p(e_dir)
      except AttributeError:
          e = None


# Not found yet, search various standard system locations.
if e is None:
    for e_path in _e_path_possibilities():
        if e_path is not None:
            try:
                e = cdll.LoadLibrary(e_path)
            except OSError:
                pass
            else:
                break


# No usable enchant install was found :-(
if e is None:
   raise ImportError("enchant C library not found")


# Define various callback function types

t_broker_desc_func = CFUNCTYPE(None,c_char_p,c_char_p,c_char_p,c_void_p)
t_dict_desc_func = CFUNCTYPE(None,c_char_p,c_char_p,c_char_p,c_char_p,c_void_p)


# Simple typedefs for readability

t_broker = c_void_p
t_dict = c_void_p

broker_list_dicts1 = e.enchant_broker_list_dicts
broker_list_dicts1.argtypes = [t_broker,t_dict_desc_func,c_void_p]
broker_list_dicts1.restype = None
def broker_list_dicts(cbfunc):
    def cbfunc1(*args):
        cbfunc(*args[:-1])
    broker_list_dicts1(e.enchant_broker_init() ,t_dict_desc_func(cbfunc1), None)

__list_dicts_result = []

def list_dicts():
    broker_list_dicts(__list_dicts_callback)
    l = [r[0] for r in __list_dicts_result]
    l.sort()
    return l

def __list_dicts_callback(tag, name, desc, file):
    tag = tag.encode("utf-8")
    name = name.encode("utf-8")
    desc = desc.encode("utf-8")
    file = file.encode("utf-8")
    __list_dicts_result.append((tag,(name,desc,file)))
