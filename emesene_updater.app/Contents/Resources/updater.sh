#!/bin/sh

#modified: 2011-05-01
#version: 2.1
#author: Josh Fradley (http://sidhosting.co.uk)

#Needs emesene.zip and update.plist on the server

workdir=`dirname $0`

#Variables
tempdir=/tmp/emeseneupdater
installpath=/Applications/emesene.app
remotepath=http://sidhosting.co.uk/download/updater
cocoadialog=$workdir/CocoaDialog.app/Contents/MacOS/CocoaDialog

#Progress bar for update check
rm -f /tmp/hpipe
mkfifo /tmp/hpipe
$cocoadialog progressbar --indeterminate --title "emesene updater" --text "Please wait..." < /tmp/hpipe &
exec 3<> /tmp/hpipe

#Make temp directory
mkdir -p $tempdir
cd $tempdir

#Check to see if emesene is installed, if not exit
if [ -d $installpath ] 
then 
  sleep 0
else
  exec 3>&-
  wait
  rm -f /tmp/hpipe
  $cocoadialog ok-msgbox --title "emesene updater" --text "emesene is not installed" --informative-text "emesene could not be found at $installpath."
  rm -r $tempdir
  exit 0
fi

#If website is 404'ing then exit
webupcheck=`curl --silent -o update.plist http://sidhosting.co.uk/download/updater/update.plist; cat update.plist`
if [[ $webupcheck == *404* ]]
then
  exec 3>&-
  wait
  rm -f /tmp/hpipe
  $cocoadialog ok-msgbox --title "emesene updater" --text "Could not check for updates" --informative-text "$remotepath is experiencing problems."
  rm -r $tempdir
  exit 0
else
  sleep 0
  rm update.plist
fi

#Check version numbers
echo -n "Checking for any available updates..." >&3
sleep 1
installedbuild=`defaults read $installpath/Contents/Info CFBundleVersion`
installedversion=`defaults read $installpath/Contents/Info CFBundleShortVersionString`
curl --silent -o update.plist $remotepath/update.plist
#FIXME: This should not need the dir passed to it
remotebuild=`defaults read $tempdir/update Build`
remoteversion=`defaults read $tempdir/update Version`
remoteismajor=`defaults read $tempdir/update IsMajor`

exec 3>&-
wait
rm -f /tmp/hpipe

if [ "$installedbuild" == "$remotebuild" ] && [ "$installedversion" == "$remoteversion" ]
then
    $cocoadialog ok-msgbox --title "emesene updater" --text "No updates available" --informative-text "You have emesene version $installedversion build $installedbuild which is the latest version available."
    rm -r $tempdir
    sleep 2
    exit 0
else
	sleep 0
fi

#Check whether we need updated dependencies
if [[ $remoteismajor == "1" ]]
then
doupdatema=`$cocoadialog yesno-msgbox --title "emesene updater" --text "An major update is available" --informative-text "emesene version $remoteversion build $remotebuild is available. The build has updated dependencies so it will need to be redownloaded. Do you wish to go to the download site now?"`
if [ "$doupdatema" == "1" ]; then
    echo "Opening download site..."
    open "http://sidhosting.co.uk/download/get.php?id=1"
    rm -r $tempdir
    exit 0
elif [ "$doupdatema" == "2" ]; then
    echo "Skipping update..."
    rm -r $tempdir
    exit 0
elif [ "$doupdatema" == "3" ]; then
    echo "Cancelling..."
    rm -r $tempdir
    exit 0
fi
else
sleep 0
fi

#Notify the user if an update is available
doupdate=`$cocoadialog yesno-msgbox --title "emesene updater" --text "An update is available" --informative-text "emesene version $remoteversion build $remotebuild is available. You currently have emesene version $installedversion build $installedbuild. Do you want to install this update?"`
if [ "$doupdate" == "1" ]; then
    echo "Continuing..."
elif [ "$doupdate" == "2" ]; then
    echo "Exiting..."
    rm -r $tempdir
    exit 0
elif [ "$doupdate" == "3" ]; then
    echo "Cancelling..."
    rm -r $tempdir
    exit 0
fi
sleep 2

#Progress bar for install
rm -f /tmp/hpipe
mkfifo /tmp/hpipe
$cocoadialog progressbar --indeterminate --title "emesene updater" --text "Please wait..." < /tmp/hpipe &
exec 3<> /tmp/hpipe

echo -n "Downloading..." >&3
curl --silent -o emesene.zip $remotepath/emesene.zip
tar -xzf emesene.zip

echo -n "Installing..." >&3
#FIXME: Permissions problem without first two rm's
rm -r $installpath/Contents/Resources/emesene/e3/papylib/papyon/.git
rm -r $installpath/Contents/Resources/emesene/e3/jabber/xmppy/.git
rm -r $installpath/Contents/Resources/emesene
mv emesene $installpath/Contents/Resources/emesene
defaults write $installpath/Contents/Info CFBundleShortVersionString -string $remoteversion
defaults write $installpath/Contents/Info CFBundleVersion -string $remotebuild
rm -r $tempdir

exec 3>&-
wait
rm -f /tmp/hpipe

$cocoadialog ok-msgbox --title "emesene updater" --text "Update complete" --informative-text "emesene has been updated to version $remoteversion build $remotebuild. Please relaunch emesene for changes to take effect."