#!/bin/sh

#Copyright 2012 The emesene team and Josh Fradley (http://blog.emesene.org)

workdir=`dirname "$0"`

cd $workdir/emesene
python emesene.py > ~/Library/Logs/emesene.log 2>&1 && exit 1