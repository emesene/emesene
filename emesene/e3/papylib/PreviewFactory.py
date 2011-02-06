''' papylib's preview factory - creates preview during file transportation '''
# -*- coding: utf-8 -*-
#
# papylib - an emesene extension for papyon
#
# Copyright (C) 2009-2010 Riccardo (C10uD) <c10ud.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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
#
# Created by Andrea Stagi <stagi.andrea(at)gmail.com>
#

import Image
import hashlib
import tempfile

def makePreview(src):

    try:
    	pbf = Image.open(src)
    except:
        return None

    pbf = pbf.resize((96, 96), Image.BILINEAR)

    filetmp = tempfile.mkstemp(prefix=hashlib.md5(src).hexdigest(), suffix=hashlib.md5(src).hexdigest())[1]

    pbf.save(filetmp,"png")
    
    out_file = open(filetmp,"rb")
    cnt = out_file.read()
    out_file.close()

    return cnt
