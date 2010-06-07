gui
---

gui is the base module that contains different implementations of the emesene
GUI with different toolkits.

emesene is structured in a way that allows multiple GUIs to be implemented
with the same functionality moving all the client logic to modules that are
toolkit independent.

base
~~~~

The base module contains all the functionality that is GUI independent and
abstract implementations that must be implemented by the toolkits.

This module contains code to handle Themes, Adium themes, to Handle the
responses from the dialogs, stock constants for things as responses and icons
and abstract classes for complex things such as ContactList, Conversation etc.

The developers should aim to move the maximum amount of code to gui.base so it
can be reused by multiple frontends and to make the toolkit dependent code as
minimal as possible.

gtkui
~~~~~

This module contains all the GTK dependent code for all the widgets that are
needed to build the GUI.

Some classes extend classes defined in gui.base, some of them are full
implementations.

The code is divided in modules that implement different widgets and are
registered as extensions for different categories, see the extension
documentation for more information about this.
