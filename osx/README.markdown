# Building emesene on OS X

## Requirements

* [gtk binary](http://sidhosting.co.uk/downloads/get.php?id=gtk) (Prebuilt binary, extract and copy into this folder)
* [Platypus](http://sveinbjorn.org/files/software/platypus.zip) (Once downloaded go to Prefs and click the install button where it says command line tool)
* git (Pretty obvious this one)

## Build latest version

```
git clone https://github.com/emesene/emesene.git
cd emesene/osx
sh build_osx.sh
```

## Build specific version

Using emesene version 2.12.5 as an example, change this to the version you want.

```
git clone https://github.com/emesene/emesene.git
git checkout v2.12.5
cd emesene/osx
sh build_osx.sh
```

You should end up with an emesene.app in the dist folder

If you are planning to release emesene at step 3, run sh build_osx.sh dorelease, this will create a folder ready to be made into a DMG.