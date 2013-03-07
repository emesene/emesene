# Building emesene on OS X

## Requirements and Information

* [gtk binary](http://www.mediafire.com/download.php?6vl96yienoiofsm) (Prebuilt binary)
* [Platypus](http://sveinbjorn.org/files/software/platypus.zip) (Once downloaded go to Prefs and click the "Install" button at the bottom to install the command line tool)
* [git](http://git-scm.com/downloads)

Before continuing, make sure the gtk binary folder is located in the emesene/osx directory

Please note emesene.app will only work if it is in /Applications!

## Building the latest version in the repo

```
git clone https://github.com/emesene/emesene.git
cd emesene/osx
sh build_osx.sh
```

This will create emesene.app in the emesene/dist directory

## Building a specific version

Using emesene version 2.12.9 as an example, change this to the version you want.

```
git clone https://github.com/emesene/emesene.git
cd emesene
git checkout v2.12.9
cd osx
sh build_osx.sh
```

This will create emesene.app in the emesene/dist directory

### Special Cases

If your building a version prior to 2.12.9 you will need to run these commands after git checkout:

```
git checkout master osx
```

Some earlier versions of emesene use submodules. If this is the case you will need to run these commands after git checkout:

```
git submodule init
git submodule update
```

You should end up with an emesene.app in the ../dist folder

### Releasing

If you are planning to release emesene run:

```
sh build_osx.sh dorelease
```

This will create a DMG for you and mount it in Finder, you can then move the icons and set the DMG background. Once that is done go back to the script and press enter. A compressed DMG will then be built in the emesene/dist folder.

### Known Issues

* Icons on the DMG have to be set manually