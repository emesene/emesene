#!/usr/bin/env sh
DATE=$(date +%F)
REPORT=$(echo -n "report$DATE")

for i in $(find . -name \*.py -not -path "*xmpp*"); do echo -n "$i, " >> $REPORT; pylint $i | tail -n 2 | awk '{print $7}' >> $REPORT; done
