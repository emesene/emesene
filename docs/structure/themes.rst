Themes
------

Themes are a way to customize the look and feel of emesene without modifying
the code.

Themes are just a defined directory structure that contains images, sounds and
other kinds of files that emesene loads and provides as an option for the user
to choose.

They can be placed into the emesene themes folder and select them in the emesene preference window.

================  ============
SO                    Path [1]_
================  ============
Windows XP          ``C:\Documents and Settings\USERNAME\Application data\emesene\emesene2\themes``
Windows Vista       ``C:\Users\USERNAME\AppData\Roaming\emesene\emesene2\themes``
Windows 7           ``C:\Users\USERNAME\AppData\Roaming\emesene\emesene2\themes``
Linux               ``~/.config/emesene2/themes (OR /home/USERNAME/.config/emesene2/themes for another user)`` [2]_
Mac                 ``~/Library/Application Support/emesene2/themes``
================  ============

.. rubric:: Notes

.. [1] replace **USERNAME** with your username on your computer
.. [2] for |2.11.4| and |2.11.5| ~/.config/emesene2/themes does not work, instead use /usr/share/emesene/emesene/themes

Conversations
~~~~~~~~~~~~~

This directory contains `Adium Style Themes`__ used by ``adium output`` extension. See the documentation for more
information about layout and formats.

`Emesene <http://blog.emesene.org/>`_ contains two default adium conversation styles **Ravenant** and **Renkoo**, but you can add
more themes instaling **emesene-supported-themes** package or from `Adium Xtras site <http://www.adiumxtras.com>`_.

__ http://trac.adium.im/wiki/CreatingMessageStyles

Emotes
~~~~~~

This directory contains the emoticons used in conversations.
`Emesene <http://blog.emesene.org/>`_ uses adium emoticon themes,
witch consist in files mapping to emoticons acording to a 
**.AdiumEmoticonSet** file.

Many Emoticon sets are available at the `Adium Xtras site <http://www.adiumxtras.com>`_.

Images
~~~~~~

This directory contains themes to change the images shown in the emesene GUI
such as emesene logo, status icons etc.

The names and sizes should be the same as the ones in the default directory.

Sounds
~~~~~~

This directory contains themes to change the sounds that are played when 
different events happen.

Sound themes should contains following files:

* alert.wav
* nudge.wav
* offline.wav
* online.wav
* send.wav
* type.wav
