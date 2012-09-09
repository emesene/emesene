#!/bin/sh

#emesene uninstaller rev 6

#Copyright Josh Fradley
#I accept no responsiblity for any damage done to your system

echo "Welcome to the emesene OS X Uninstaller"
read -p "Press enter to continue..."

#Check if emesene actually exists
if [ -d "/Applications/emesene.app" ]
then
    echo "Starting Uninstall..."
else
    echo "emesene is not installed..."
    exit
fi

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