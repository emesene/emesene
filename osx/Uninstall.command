#!/bin/sh

#emesene uninstaller rev 7

#Copyright Josh Fradley
#I accept no responsiblity for any damage done to your system

#Check if emesene actually exists
if [ -d "/Applications/emesene.app" ]
then
    continue
else
    echo "emesene is not installed..."
    exit
fi

echo "Welcome to the emesene OS X uninstaller"
read -p "Press enter to continue..."

#Kill emesene if it is running
isrunning=`ps -cx | grep "emesene"`
if [ -z "$isrunning" ]
then
    continue
else
    killall emesene
    killall python
fi

#emesene files
rm -rf "/Applications/emesene.app"
rm -rf "/Users/$USER/Library/Caches/org.emesene.emesene" 
rm -f "/Users/$USER/Library/Preferences/org.emesene.emesene.plist" 
rm -f "/Users/$USER/Library/Preferences/org.emesene.emesene.plist.lockfile"
rm -rf "/Users/$USER/Library/Saved Application State/org.emesene.emesene.savedState"
rm -f "/Users/$USER/Library/Application Support/Growl/Tickets/emesene.growlTicket"
getid=`sqlite3 ~/Library/Containers/com.Growl.GrowlHelperApp/Data/Library/Application\ Support/Growl/tickets.database "SELECT Z_OPT FROM ZGROWLTICKET WHERE ZNAME = emesene"`
sqlite3 ~/Library/Containers/com.Growl.GrowlHelperApp/Data/Library/Application\ Support/Growl/tickets.database "SELECT * FROM ZGROWLTICKET WHERE Z_OPT = $getid" 

#gtk files
rm -rf "/Users/$USER/.config/gtk-2.0" 

#user settings
echo "Remove user settings?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) rm -rf "/Users/$USER/Library/Application Support/emesene2"; break;;
        No ) break;;
    esac
done

echo "emesene has been successfully uninstalled..."