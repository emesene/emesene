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
rm -rf /tmp/emesene
rm -rf ../dist

#Create /tmp/emesene dir
#We have to work outside ../dist because patch will fail otherwise
mkdir /tmp/emesene

#Build the app with Platypus
/usr/local/bin/platypus -i 'emesene.icns' -a 'emesene' -V ''$version'' -o 'None' -p '/bin/sh' -u 'The emesene team and Josh Fradley' -I org.emesene.emesene -R 'emesene.sh' '/tmp/emesene/emesene.app'

echo "Bundling GTK..."
cp -r gtk /tmp/emesene/emesene.app/Contents/Resources/

echo "Bundling emesene..."
cp -r ../emesene /tmp/emesene/emesene.app/Contents/Resources/

echo "Patching emesene..."
patch /tmp/emesene/emesene.app/Contents/Resources/emesene/emesene.py < emesenepygtkpatch.patch

defaults write /tmp/emesene/emesene.app/Contents/Info LSMinimumSystemVersion -string "10.6"

mkdir ../dist

if [[ "$1" == *dorelease* ]]
then
    #Last stable
    mkdir ../dist/emesene
    mv /tmp/emesene/emesene.app ../dist/emesene
    cp Uninstall.command ../dist/emesene
    mkdir ../dist/emesene/.background
    ln -s /Applications ../dist/emesene
    cp emesenedmg.png ../dist/emesene/.background
    chmod +x ../dist/emesene/Uninstall.command
else
    mv /tmp/emesene/emesene.app ../dist
fi

echo "Successfully built emesene $version".