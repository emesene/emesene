#!/usr/bin/env python
'''Language module, allows the user to change the language on demand'''
# -*- coding: utf-8 -*-

#    This file is part of emesene.
#
#    emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gettext
import locale
import glob


class Language(object):
    """
    A class for language management
    """
    NAME = 'Language'
    DESCRIPTION = 'Language management module'
    AUTHOR = 'Lucas F. Ottaviano (lfottaviano)'
    WEBSITE = 'www.emesene.org'

    def __init__(self):
        """ constructor """
        self._languages = None

        self._translation = gettext.NullTranslations()

        self._default_locale = locale.getdefaultlocale()[0]
        self._lang = os.getenv('LANGUAGE') or self._default_locale
        self._locales_path = 'po/' if os.path.exists('po/') else None

        self._get_languages_list()

    def install_desired_translation(self,  language):
        """
        installs translation of the given @language
        """
        self._lang = language

        if self._lang in self._languages:
            self._translation = gettext.translation('emesene',
                                            localedir=self._locales_path,
                                            languages=[self._lang])
        else:

            # if language code isn't available and is for example
            # es_UY, split and use only "es".
            self._translation = gettext.translation('emesene',
                                        localedir=self._locales_path,
                                        languages=[self._lang.split("_")[0]], 
                                        fallback=True)

            if not isinstance(self._translation, gettext.GNUTranslations):
                #try with Python's locale module     
                self._translation = gettext.translation('emesene',
                                        localedir=self._locales_path,
                                        languages=[self._default_locale],
                                        fallback=True)

            if not isinstance(self._translation, gettext.GNUTranslations):
                #let gettext handle the language
                self._translation = gettext.translation('emesene',
                                        localedir=self._locales_path, 
                                        fallback=True)

        self._translation.install()


    def install_default_translation(self):
        """
        installs a translation relative to system enviroment
        """
        language = os.getenv('LANGUAGE') or self._default_locale
        self.install_desired_translation(language)

    # Getters
    def get_default_locale(self):
        """
        returns default locale obtained assigned only on object instantiation
        from locale python module
        """
        return self._default_locale

    def get_lang(self):
        """
        returns the current language code that has been used for translation
        """
        return self._lang

    def get_locales_path(self):
        """
        returns the locales path
        """
        return self._locales_path

    def get_current_translation(self):
        """
        returns the translation object
        """
        return self._translation

    def get_available_languages(self):
        """ returns a list of available languages """
        return self._get_languages_list()

    def _get_languages_list(self):
        """ fills languages list"""
        if self._languages is None:
            paths = glob.glob(os.path.join(self._locales_path, '*',
                                      'LC_MESSAGES', 'emesene.mo'))

            self._languages = [path.split(os.path.sep)[-3] for path in paths]
            self._languages.sort()

        return self._languages
