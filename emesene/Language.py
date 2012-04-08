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
    LANGUAGES_DICT = {'af':'Afrikaans',
      'ar':'\xd8\xa7\xd9\x84\xd8\xb9\xd8\xb1\xd8\xa8\xd9\x8a\xd8\xa9',
      'ast':'Asturianu',
      'az':'\xd8\xa2\xd8\xb0\xd8\xb1\xd8\xa8\xd8\xa7\xdb\x8c\xd8\xac\xd8\xa7\xd9\x86 \xd8\xaf\xdb\x8c\xd9\x84\xdb\x8c',
      'bg':'\xd0\x91\xd1\x8a\xd0\xbb\xd0\xb3\xd0\xb0\xd1\x80\xd1\x81\xd0\xba\xd0\xb8 \xd0\xb5\xd0\xb7\xd0\xb8\xd0\xba',
      'bn':'\xe0\xa6\xac\xe0\xa6\xbe\xe0\xa6\x82\xe0\xa6\xb2\xe0\xa6\xbe',
      'bs':'\xd0\xb1\xd0\xbe\xd1\x81\xd0\xb0\xd0\xbd\xd1\x81\xd0\xba\xd0\xb8',
      'ca':'Catal\xc3\xa0',
      'cs':'\xc4\x8de\xc5\xa1tina',
      'da':'Danish',
      'de':'Deutsch',
      'dv':'\xde\x8b\xde\xa8\xde\x88\xde\xac\xde\x80\xde\xa8',
      'el':'\xce\x95\xce\xbb\xce\xbb\xce\xb7\xce\xbd\xce\xb9\xce\xba\xce\xac',
      'en':'English',
      'en_AU':'English (Australia)',
      'en_CA':'English (Canada)',
      'en_GB':'English (United Kingdom)',
      'eo':'Esperanto',
      'es':'Espa\xc3\xb1ol',
      'et':'Eesti keel',
      'eu':'Euskara',
      'fi':'Suomi',
      'fil':'Filipino',
      'fo':'F\xc3\xb8royskt',
      'fr':'Fran\xc3\xa7ais',
      'ga':'Gaeilge',
      'gl':'Galego',
      'gv':'Gaelg',
      'he':'\xd7\xa2\xd6\xb4\xd7\x91\xd6\xb0\xd7\xa8\xd6\xb4\xd7\x99\xd7\xaa',
      'hr':'Hrvatski',
      'hu':'Magyar',
      'ia':'Interlingua',
      'id':'Bahasa Indonesia',
      'is':'\xc3\x8dslenska',
      'it':'Italiano',
      'ja':'\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e',
      'kab':'Taqbaylit',
      'kn':'Kanna\xe1\xb8\x8da',
      'ko':'\xed\x95\x9c\xea\xb5\xad\xec\x96\xb4/\xec\xa1\xb0\xec\x84\xa0\xeb\xa7\x90',
      'ku':'\xda\xa9\xd9\x88\xd8\xb1\xd8\xaf\xdb\x8c',
      'la':'Lat\xc4\xabna',
      'lb':'L\xc3\xabtzebuergesch',
      'lt':'Lietuvi\xc5\xb3',
      'lv':'Latvie\xc5\xa1u valoda',
      'mk':'\xd0\x9c\xd0\xb0\xd0\xba\xd0\xb5\xd0\xb4\xd0\xbe\xd0\xbd\xd1\x81\xd0\xba\xd0\xb8 \xd1\x98\xd0\xb0\xd0\xb7\xd0\xb8\xd0\xba',
      'ms':'\xd8\xa8\xd9\x87\xd8\xa7\xd8\xb3 \xd9\x85\xd9\x84\xd8\xa7\xd9\x8a\xd9\x88',
      'nan':'\xe9\x96\xa9\xe5\x8d\x97\xe8\xaa\x9e / \xe9\x97\xbd\xe5\x8d\x97\xe8\xaf\xad',
      'nb':'Norwegian Bokm\xc3\xa5l',
      'nds':'Plattd\xc3\xbc\xc3\xbctsch',
      'nl':'Nederlands',
      'nn':'Norwegian Nynorsk',
      'oc':'Occitan (post 1500)',
      'pl':'J\xc4\x99zyk Polski',
      'pt':'Portugu\xc3\xaas',
      'pt_BR':'Portugu\xc3\xaas Brasileiro',
      'ro':'Rom\xc3\xa2n\xc4\x83',
      'ru':'\xd1\x80\xd1\x83\xd1\x81\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9 \xd1\x8f\xd0\xb7\xd1\x8b\xd0\xba',
      'sk':'Sloven\xc4\x8dina',
      'sl':'Sloven\xc5\xa1\xc4\x8dina',
      'sq':'Shqip',
      'sr':'\xd1\x81\xd1\x80\xd0\xbf\xd1\x81\xd0\xba\xd0\xb8',
      'sv':'Svenska',
      'ta':'\xe0\xae\xa4\xe0\xae\xae\xe0\xae\xbf\xe0\xae\xb4\xe0\xaf\x8d',
      'th':'\xe0\xb8\xa0\xe0\xb8\xb2\xe0\xb8\xa9\xe0\xb8\xb2\xe0\xb9\x84\xe0\xb8\x97\xe0\xb8\xa2',
      'tr':'T\xc3\xbcrk\xc3\xa7e',
      'uk':'\xd1\x83\xd0\xba\xd1\x80\xd0\xb0\xd1\x97\xcc\x81\xd0\xbd\xd1\x81\xd1\x8c\xd0\xba\xd0\xb0 \xd0\xbc\xd0\xbe\xcc\x81\xd0\xb2\xd0\xb0',
      'vec':'V\xc3\xa8neto',
      'zh_CN':'\xe7\xae\x80\xe4\xbd\x93\xe5\xad\x97',
      'zh_HK':'\xe6\xb1\x89\xe8\xaf\xad/\xe6\xbc\xa2\xe8\xaa\x9e (\xe9\xa6\x99\xe6\xb8\xaf\xe4\xba\xba)',
      'zh_TW':'\xe7\xb9\x81\xe9\xab\x94\xe4\xb8\xad\xe6\x96\x87'}

    LANGUAGES_DICT_R = {}
    for key,value in LANGUAGES_DICT.iteritems():  
        LANGUAGES_DICT_R[value] = key

    def __init__(self):
        """ constructor """
        self._languages = None

        self._default_locale = locale.getdefaultlocale()[0]
        self._lang = os.getenv('LANGUAGE') or self._default_locale
        self._locales_path = 'po/' if os.path.exists('po/') else None

        self._get_languages_list()

    def install_desired_translation(self,  language):
        """
        installs translation of the given @language
        @language, a string with the language code or None
        """
        if language is not None:
          #if default_locale is something like es_UY or en_XX, strip the end 
          #if it's not in LANGUAGES_DICT
          if language not in self.LANGUAGES_DICT.keys():
              language = language.split("_")[0]

          self._lang = language

          # gettext.translation() receives a _list_ of languages, so make it a list.
          language = [language]

        #now it's a nice language in LANGUAGE_DICT or, if not, it's english or
        #some unsupported translation so we fall back to english in those cases
        translation = gettext.translation('emesene',
                                          localedir=self._locales_path,
                                          languages=language,
                                          fallback=True)
                                          
        if isinstance(translation, gettext.NullTranslations):
            self._lang = 'en'

        translation.install()

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

    def get_available_languages(self):
        """ returns a list of available languages """
        return self._get_languages_list()

    def _get_languages_list(self):
        """ fills languages list"""
        if self._languages is None:
            paths = glob.glob(os.path.join(self._locales_path, '*',
                                      'LC_MESSAGES', 'emesene.mo'))

            self._languages = [path.split(os.path.sep)[-3] for path in paths]
            self._languages.append('en')
            self._languages.sort()

        return self._languages
