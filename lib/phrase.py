#!/usr/bin/env python2.4
# -*- coding: utf-8 -*-
#  Copyright (C) 2007 Jacek Śliwerski (rzyjontko)
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.  

import re

class GenericHandler:
    def __init__(self, connectors):
        self._connectors = set()
        for word in connectors:
            self._connectors.add(word)

    def discard(self, word):
        return word in self._connectors
        

class PLHandler(GenericHandler):
    def __init__(self):
        GenericHandler.__init__(self, ["by"])
#["albo", "ale", "bądź", "bo", "bowiem", "by", "chociaż", "choć", "czy", "do", "jednak", "lecz", "li", "lub", "na", "nad", "niech", "od", "oraz", "po", "pod", "ponieważ", "poza", "przed", "przy", "również", "toteż", "we", "za", "zatem", "ze", "że"])

class DEHandler(GenericHandler):
    def __init__(self):
        GenericHandler.__init__(self, ["das", "dem", "den", "der", "deren", "des", "dessen", "die", "ein", "eine", "einem", "einen"])
#["aber", "als", "auch", "bevor", "da", "dann", "das", "dass", "dem", "den", "denn", "der", "deren", "des", "dessen", "die", "ein", "eine", "einem", "einen", "doch", "hinter", "jedoch", "mit", "nach", "neben", "noch", "ob", "obwohl", "oder", "seit", "so", "sowohl", "sondern", "trotz", "trotzdem", "und", "unter", "űber", "vor", "weder", "weil", "werden", "zwar"])

class ENHandler(GenericHandler):
    def __init__(self):
        GenericHandler.__init__(self, ["a", "an", "the"])
#["above", "also", "although", "an", "and", "as", "away", "because", "behind", "below", "but", "for", "from", "in", "if", "of", "off", "on", "over", "since", "so", "that", "the", "then", "though", "through", "to", "too", "under", "up", "with"])

    

class Phrase:
    wre = re.compile('\w(?:[\-&\']?\w)*', re.UNICODE)
    dre = re.compile('^\d+$', re.UNICODE)

    __handlers = { "C"  : ENHandler (),
                   "en" : ENHandler (),
                   "pl" : PLHandler (),
                   "de" : DEHandler () }
    __def_handler = GenericHandler ([])

    def __resolve(self, lang):
        if lang in self.__handlers:
            return self.__handlers[lang]
        else:
            return self.__def_handler

    def __filterfun(self, word, handler):
        return len(word) < 50 and not re.match(self.dre, word) and not handler.discard(word)

    def __init__(self, phrase, lang, sort=True):
        handler = self.__resolve (lang)
        self._phrase = phrase
        self._wordlist = filter(lambda x: self.__filterfun(x, handler), \
                                map(lambda x: x.lower(), \
                                    self.wre.findall(phrase)))
        if sort:
            self._wordlist.sort()

    def length(self):
        return len(self._wordlist)
    
    def canonical(self):
        return reduce (lambda x, y: x + ' ' + y, self._wordlist, '').lstrip()

    def canonical_list(self):
        return self._wordlist
