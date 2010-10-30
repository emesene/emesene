Como generar archivos .exe e instaladores para una aplicación python
====================================================================

Este documento describe los pasos necesarios para crear un archivo ejecutable
de una aplicación python y como generar un instalador y una versión portable
para dicha instalación.

Este documento asume que la aplicación se basa en GTK pero debería funcionar
con menores cambios en otros toolkits.

porque un instalador
--------------------

* se requiere instalar muchos componentes a mano por el usuario final para una sola aplicación
* muchos instaladores pequeños
* difíciles de encontrar
* difícil encontrar las versiones exactas que funcionan en conjunto
* requiere instalarlos en un orden definido
* rezar
* algunas veces incluso haciendo todo bien puede no funcionar
* fácil de automatizar y documentar para replicar con cada nueva versión
* liberar al usuario final de los problemas para poder usar la aplicación

componentes requeridos
----------------------

* python
* todas las librerías utilizadas por la aplicación
* py2exe
* nsis
* tiempo y suerte

instaladores
------------

aquí se listan los links a los instaladores de todos los componentes usados en el ejemplo.

* http://python.org/ftp/python/2.6.6/python-2.6.6.msi
* http://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/py2exe-0.6.9.win32-py2.6.exe/download
* http://ftp.gnome.org/pub/GNOME/binaries/win32/pycairo/1.8/pycairo-1.8.6.win32-py2.6.exe
* http://ftp.gnome.org/pub/GNOME/binaries/win32/pygobject/2.20/pygobject-2.20.0.win32-py2.6.exe
* http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.16/pygtk-2.16.0+glade.win32-py2.6.exe
* http://sourceforge.net/projects/pywin32/files/pywin32/Build%20214/pywin32-214.win32-py2.6.exe/download
* http://sourceforge.net/projects/gtk-win/files/GTK%2B%20Runtime%20Environment/GTK%2B%202.22/gtk2-runtime-2.22.0-2010-10-01-ash.exe/download
* http://sourceforge.net/projects/gtk-win/files/GTK%2B%20Themes%20Package/2009-09-07/gtk2-themes-2009-09-07-ash.exe/download
* http://prdownloads.sourceforge.net/nsis/nsis-2.46-setup.exe?download

orden de instalación
--------------------

algunos instaladores son independientes de otros, pero para evitar posibles problemas recomiendo la instalación en el siguiente orden.

* python
* gtk-runtime
* gtk2-themes
* nsis
* pygobject
* pycairo
* pygtk
* pywin32
* py2exe

tareas extra
------------

* setear la variable de entorno PATH para agregar el path a la instalación de python
* probar la instalación con una pequeña aplicación gtk

::

        >>> import gtk
        >>> w = gtk.Window()
        >>> l = gtk.Label("asd")
        >>> w.add(l)
        >>> w.show_all()
        >>> gtk.main()

prueba con una aplicación de ejemplo
------------------------------------

Cree un repositorio con una aplicación de ejemplo para probar los pasos, la aplicación esta disponible en github acá:

http://github.com/marianoguerra/PyGtkOnWindows

pasos
:::::

* descargarla
* descomprimirla
* ejecutar python setup.py py2exe
* copiar los directorios lib y share de la instalación del runtime de gtk (no de la instalación de pygtk) al directorio dist
* copiar todos los archivos del directorio dll al directorio dist
* borrar los locales y temas no usados de los directorios copiados a dist (yo solo dejo el theme MS-Windows)
* crear la siguiente estructura de directorios dentro de dist: etc/gtk-2.0
* dentro de ese directorio crear un archivo llamado gtkrc con una linea como la siguiente dentro:

  * gtk-theme-name = "MS-Windows"
  * podes cambiar el tema usado manteniendo otro theme dentro de share/themes y cambiando el nombre del theme en gtkrc

* right click en ejemplo.nsi y seleccionar "Compile NSIS Script"
* right click en ejemplo-portable.nsi y seleccionar "Compile NSIS Script"
* deberías tener el instalador y la versión portable disponibles
* para probar que funciona correctamente, correr el instalador y la versión portable en una instalación de windows sin los paquetes que instalaste anteriormente

probar con una aplicación real
------------------------------

ahora para sentirlo mas real, creemos un instalador y una versión portable de
un programa real, en este caso, un proyecto personal llamado emesene 2
(http://www.emesene.org/).

pasos
:::::

* descargarlo de http://github.com/emesene/emesene
* descomprimirlo
* copiar setup.py and ez_setup.py al directorio emesene
* cd emesene
* correr python setup.py py2exe
* cd ..
* copiar los directorios lib y share de la instalación del runtime de gtk (no de la instalación de pygtk) al directorio dist
* copiar todos los archivos del directorio dll al directorio dist
* borrar los locales y temas no usados de los directorios copiados a dist (yo solo dejo el theme MS-Windows)
* crear la siguiente estructura de directorios dentro de dist: etc/gtk-2.0
* dentro de ese directorio crear un archivo llamado gtkrc con una linea como la siguiente dentro:

  * gtk-theme-name = "MS-Windows"
  * podes cambiar el tema usado manteniendo otro theme dentro de share/themes y cambiando el nombre del theme en gtkrc

* right click en emesene.nsi y seleccionar "Compile NSIS Script"
* right click en emesene-portable.nsi y seleccionar "Compile NSIS Script"
* deberías tener el instalador y la versión portable disponibles
* para probar que funciona correctamente, correr el instalador y la versión portable en una instalación de windows sin los paquetes que instalaste anteriormente

notas
-----

* obtengo algunos de los dlls requeridos de portable python (http://www.portablepython.com/) e inkscape (http://inkscape.org/)

