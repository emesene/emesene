How to generate .exe files and installers for a python applications
===================================================================

This document describes the steps required to create an executable file from a
python program and how to build an installer and portable file from that
application.

The document assumes that the application is based on GTK but it should work
with minor changes for other toolkits.

why an installer
----------------

* many components are required to install by hand by the end user for a simple application
* a lot of small installers
* hard to find
* hard to match the exact versions that work together
* install them in the required order
* pray
* sometimes even doing everything right it may not work
* easy to automate and document to replicate with each new version
* free the end user from problems to use the app

required components
-------------------

* python
* all the libraries used by the application
* py2exe
* nsis
* time and luck ;)

installers
----------

here are listed the links to the installers of all the components used in the example.

* http://python.org/ftp/python/2.6.6/python-2.6.6.msi
* http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/py2exe-0.6.9.win32-py2.6.exe/download
* http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.8/pycairo-1.8.6.win32-py2.6.exe
* http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.20/pygobject-2.20.0.win32-py2.6.exe
* http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.16/pygtk-2.16.0+glade.win32-py2.6.exe
* http://sourceforge.net/projects/pywin32/files/pywin32/Build%20214/pywin32-214.win32-py2.6.exe/download
* http://sourceforge.net/projects/gtk-win/files/GTK%2B%20Runtime%20Environment/GTK%2B%202.22/gtk2-runtime-2.22.0-2010-10-01-ash.exe/download
* http://sourceforge.net/projects/gtk-win/files/GTK%2B%20Themes%20Package/2009-09-07/gtk2-themes-2009-09-07-ash.exe/download
* http://prdownloads.sourceforge.net/nsis/nsis-2.46-setup.exe?download

installation order
------------------

some installers are independent from the others, but to avoid posible problems I recommend the installation in this order.

* python
* gtk-runtime
* gtk2-themes
* nsis
* pygobject
* pycairo
* pygtk
* pywin32
* py2exe

extra tasks
-----------

* set the PATH environment variable to add the path to the python installation
* test that the installation works with a simple gtk application

::

        >>> import gtk
        >>> w = gtk.Window()
        >>> l = gtk.Label("asd")
        >>> w.add(l)
        >>> w.show_all()
        >>> gtk.main()

test with a sample application
------------------------------

I created a repository with a sample application to test the steps, the application is available in github here:

http://github.com/marianoguerra/PyGtkOnWindows

steps
:::::

* download it
* unpack it
* run python setup.py py2exe
* copy the lib and share directory from the gtk runtime installation  (not the pygtk installation) to the dist directory
* copy all the files from the dll directory to the dist directory
* remove unused locales and unused themes (I keep only ms theme)
* create the following dirs inside dist: etc/gtk-2.0
* inside that create a file called gtkrc with a line like this inside:

  * gtk-theme-name = "MS-Windows"
  * you can change the theme by keeping that theme inside share/themes and changing the name in gtkrc

* right click on ejemplo.nsi and select "Compile NSIS Script"
* right click on ejemplo-portable.nsi and select "Compile NSIS Script"
* you should have the installer and portable versions available
* to test that it works correctly, run the installer and portable versions in a windows installation without the packages you installed previously

test with a real application
----------------------------

now to make it feel more real let's create an installer and portable versions
for a real world program, in this case, a project of mine called emesene 2
(http://www.emesene.org/).

steps
:::::

* download it from http://github.com/emesene/emesene
* unpack it
* copy setup.py and ez_setup.py to the emesene directory
* cd to emesene
* run python setup.py py2exe
* cd ..
* copy the lib and share directory from the gtk runtime installation  (not the pygtk installation) to the dist directory
* copy all the files from the dll directory to the dist directory
* remove unused locales and unused themes (I keep only ms theme)
* create the following dirs inside dist: etc/gtk-2.0
* inside that create a file called gtkrc with a line like this inside:

  * gtk-theme-name = "MS-Windows"
  * you can change the theme by keeping that theme inside share/themes and changing the name in gtkrc

* right click on emesene.nsi and select "Compile NSIS Script"
* right click on emesene-portable.nsi and select "Compile NSIS Script"
* you should have the installer and portable versions available
* to test that it works correctly, run the installer and portable versions in a windows installation without the packages you installed previously

notes
-----

* I get some needed dlls from portable python (http://www.portablepython.com/) and inkscape (http://inkscape.org/)

