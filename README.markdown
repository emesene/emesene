# emesene

emesene is an instant messenger capable of connecting to various networks
and utilizing different graphical toolkits.
Currently msn and xmpp (jabber) are supported through papyon and SleekXMPP,
which allows emesene to connect to various IM services such as
Windows Live Messenger, GTalk, Facebook Chat, etc.

## Useful links

* [Main repository](http://github.com/emesene/emesene) (fork this one)
* [Wiki](http://wiki.github.com/emesene/emesene)
* [Issue tracker](http://github.com/emesene/emesene/issues)

## Upstream libraries repositories

emesene embeds in its codebase a number of python libraries for the different
service it supports. We embed them instead of using git submodules so we can
make packagers' life better and hotfix eventual bugs.

* [papyon] (https://github.com/emesene/papyon)
* [SleekXMPP] (https://github.com/fritzy/SleekXMPP)
* [pyfb] (https://github.com/jmg/pyfb)
