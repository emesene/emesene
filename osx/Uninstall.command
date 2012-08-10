#!/bin/sh

#emesene uninstaller rev 5

#Copyright Josh Fradley
#I accept no responsiblity for any damage done to your system

echo "Welcome to the emesene uninstaller"
read -p "Press enter to continue..."

#Check if emesene actually exists
if [ -d "/Applications/emesene.app" ]
then
    echo "Starting uninstall..."
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
rm -f "/Users/$USER/Library/Application Support/Growl/Tickets/emesene.growlTicket" 

#Remove OS X 10.7 specific files
os=`sw_vers -productVersion`
if [[ "$os" == *10.7* ]]
then
    rm -rf "/Users/$USER/Library/Saved Application State/org.emesene.emesene.savedState" 
    rm -f "/Users/$USER/Library/Preferences/org.emesene.emesene.plist.lockfile"
else
    continue
fi

#gtk files
rm -rf "/Users/$USER/.config/gtk-2.0" 

#user settings
echo "Remove user settings? Type 'yes' if you wish to remove them. If not type anything else..."
read doremoveusersettings

if [ "$doremoveusersettings" == "yes" ]
then
    rm -rf "/Users/$USER/Library/Application Support/emesene2"
else
    continue
fi

echo "emesene has been successfully uninstalled..."