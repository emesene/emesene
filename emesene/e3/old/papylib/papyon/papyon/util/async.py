# -*- coding: utf-8 -*-
#
# papyon - a python client library for Msn
#
# Copyright (C) 2010 Collabora Ltd.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import logging

logger = logging.getLogger("papyon.util.async")

__all__ = ["run"]

def is_valid_callback(callback):
    return (isinstance(callback, tuple) and len(callback) > 0 and
            callback[0] is not None and callable(callback[0]))

def run(callback, *args):
    if callback is None:
        return
    if not is_valid_callback(callback):
        import traceback
        traceback.print_stack()
        logger.error("Invalid callback %s" % repr(callback))
        return
    args = tuple(args) + tuple(callback[1:])
    callback[0](*args)
