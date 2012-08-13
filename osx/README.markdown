# Building emesene on OS X

## Requirements

* [gtk binary](http://sidhosting.co.uk/downloads/get.php?id=gtk) (Prebuilt binary)
* [Platypus](http://sveinbjorn.org/files/software/platypus.zip) (Once downloaded go to Prefs and click the "Install" button at the bottom)
* [git] (http://git-scm.com/downloads)

## Building the latest version

```
git clone https://github.com/emesene/emesene.git
cd emesene/osx
```

Now drag the gtk folder you downloaded earlier into the osx directory.

```
sh build_osx.sh
```

## Building a specific version

Using emesene version 2.12.5 as an example, change this to the version you want.

```
git clone https://github.com/emesene/emesene.git
cd emesene
git checkout v2.12.5
cd osx
```

Now drag the gtk folder you downloaded earlier into the osx directory.

```
sh build_osx.sh
```
### Special Cases

If your building a version prior to 2.12.6 you will need to run these commands after git checkout:
```
git checkout master osx
```

Some earlier versions of emesene use submodules. If this is the case you will need to run these commands after git checkout:

```
git submodule init
git submodule update
```

You should end up with an emesene.app in the ../dist folder

If you are planning to release emesene, run sh build_osx.sh dorelease, this will create a folder ready to be made into a DMG.

### Caveats

* DMG has to be built manually, just create a new disk image from the dist/emesene folder. The background image is in dist/emesene/.background
* DMG volume icon has to be set manually