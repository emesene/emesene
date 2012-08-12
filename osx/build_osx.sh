#!/bin/sh

#Dont use this unless you know what your doing!
#Comes with absolutely no warranty!

version=`grep 'EMESENE_VERSION = ".*"' ../emesene/Info.py | cut -d '"' -f 2`
    
echo "############################################################################"
echo "### Welcome to the emesene builder. Version 3.2.0 Copyright Josh Fradley ###" 
echo "############################################################################"

echo "Preparing to build emesene $version. Press enter to continue..."
read

#Remove old builds
rm -rf ../dist

#Create temp dir
mkdir ../dist

#Build the app with Platypus
/usr/local/bin/platypus -i 'emesene.icns' -a 'emesene' -V ''$version'' -o 'None' -p '/bin/sh' -u 'The emesene team and Josh Fradley' -I org.emesene.emesene -R 'emesene.sh' '../dist/emesene.app'

echo "Bundling GTK..."
cp -r gtk ../dist/emesene.app/Contents/Resources/

echo "Bundling emesene..."
cp -r ../emesene ../dist/emesene.app/Contents/Resources/

defaults write ${PWD}/../dist/emesene.app/Contents/Info LSMinimumSystemVersion -string "10.6"

if [[ "$1" == *dorelease* ]]
then
    #Last stable
    mkdir ../dist/emesene
    mv ../dist/emesene.app ../dist/emesene
    cp Uninstall.command ../dist/emesene
    chmod +x ../dist/emesene/Uninstall.command
    ln -s /Applications ../dist/emesene
    mkdir ../dist/emesene/.background
    cp emesenedmg.png ../dist/emesene/.background
fi

echo "Successfully built emesene $version".