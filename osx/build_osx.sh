#!/bin/sh

#Dont use this unless you know what your doing!
#Comes with absolutely no warranty!

version=`grep 'EMESENE_VERSION = ".*"' ../emesene/Info.py | cut -d '"' -f 2`
    
echo "############################################################################"
echo "### Welcome to the emesene builder. Version 3.4.0 Copyright Josh Fradley ###" 
echo "############################################################################"

read -p "Preparing to build emesene $version. Press enter to continue..."

#Remove old builds
rm -rf ../dist

#Create temp dir
mkdir ../dist

#Build the app with Platypus
echo "Building app..."
/usr/local/bin/platypus -i 'emesene.icns' -a 'emesene' -o 'None' -p '/bin/sh' -u 'The emesene team and Josh Fradley' -I org.emesene.emesene -R 'emesene.sh' '../dist/emesene.app' > /dev/null 2>&1

echo "Setting version..."
#There is a bug in Platypus which sets CFBundle rather than CFBundleShortVersionString, should be fixed in Platypus 4.8
defaults write ${PWD}/../dist/emesene.app/Contents/Info CFBundleVersion -string "340"
defaults write ${PWD}/../dist/emesene.app/Contents/Info CFBundleShortVersionString -string "$version"

echo "Bundling GTK..."
cp -r gtk ../dist/emesene.app/Contents/Resources/

echo "Bundling emesene..."
cp -r ../emesene ../dist/emesene.app/Contents/Resources/

defaults write ${PWD}/../dist/emesene.app/Contents/Info LSMinimumSystemVersion -string "10.6"

if [[ "$1" == *dorelease* ]]
then
    mkdir ../dist/emesene
    mv ../dist/emesene.app ../dist/emesene
    cp Uninstall.command ../dist/emesene
    chmod +x ../dist/emesene/Uninstall.command
    ln -s /Applications ../dist/emesene
    cp emesenedmg.png ../dist/emesene
    cp VolumeIcon.icns ../dist/emesene/.VolumeIcon.icns
    hdiutil detach -quiet /Volumes/emesene
    hdiutil create -quiet ${PWD}/../dist/emesenetemp.dmg -srcfolder ${PWD}/../dist/emesene -volname emesene -format UDRW -ov
    hdiutil attach -quiet ${PWD}/../dist/emesenetemp.dmg
    SetFile -c icnC /Volumes/emesene/.VolumeIcon.icns
    SetFile -a C /Volumes/emesene
    read -p "Please set the background and icon location now, this must be done manually. Then come back here and hit enter..."
    SetFile -a V /Volumes/emesene/emesenedmg.png
    hdiutil detach -quiet /Volumes/emesene
    dmgversion=`echo $version | tr -d "."`
    hdiutil convert ${PWD}/../dist/emesenetemp.dmg -format UDZO -imagekey zlib-level=9 -quiet -o ${PWD}/../dist/emesene$dmgversion.dmg
    rm ../dist/emesenetemp.dmg
fi

echo "Successfully built emesene $version"