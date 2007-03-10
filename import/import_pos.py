#/usr/bin/python2.4
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

import gettext2, string, sys, dircache

from phrase import Phrase
from pysqlite2 import dbapi2 as sqlite

conn = sqlite.connect('../data/fifth.db')
cursor = conn.cursor()



class Project:
    def __init__(self, name):
        self._name = name
        self._phrases = {}
    
    def read_file(self, fname, lang):
        try:
            trans = gettext2.GNUTranslations(open(fname, 'rb'))
        except Exception:
            return
        for k, v in trans.catalog.iteritems():
            if type(k) is type(u''):
                msg = k
            else:
                msg, n = k
                if n > 0:
                    continue
            ts = self._phrases.setdefault(msg, {})
            ts[lang] = v

    def _read_mo(self, lang):
        self._read_file('/usr/share/locale/' + lang + '/LC_MESSAGES/' + self._name + '.mo', lang)

    def read_selected(self, langs):
        for lang in langs:
            try:
                self._read_mo(lang)
            except IOError:
                pass

    def read_all(self):
        self.read_selected(dircache.listdir('/usr/share/locale'))

    def _store_location(self):
        cursor.execute(u"insert into locations (project) values (?)", (self._name,))
        cursor.execute("select max (rowid) from locations")
        return cursor.fetchone()[0]

    def _store_phrase(self, lid, lang, sentence):
        phrase = Phrase (sentence, lang)
        if phrase.length () < 1:
            return
        cursor.execute(u"insert into phrases(locationid, lang, phrase) values (?, ?, ?)", \
                       (lid, lang, sentence))
        cursor.execute(u"insert into canonical(locationid, lang, phrase) values (?, ?, ?)", \
                       (lid, lang, phrase.canonical ()))
        #cursor.execute("select max (rowid) from canonical")
        #canonicalid = cursor.fetchone()[0]
        #last = 0
        #for i in range(1, phrase.length ()):
        #    if phrase.canonical_list ()[i] != phrase.canonical_list ()[last]:
        #        cursor.execute(u"insert into words (word, canonicalid, count) values (?, ?, ?)", \
        #                       (phrase.canonical_list ()[last], canonicalid, i - last))
        #cursor.execute(u"insert into words (word, canonicalid, count) values (?, ?, ?)", \
        #               (phrase.canonical_list ()[phrase.length () - 1], canonicalid, phrase.length () - last))

    def store(self):
        i = 0
        for k, v in self._phrases.iteritems():
            loc_id = self._store_location()
            self._store_phrase(loc_id, 'C', k)
            for lang, sentence in v.iteritems():
                self._store_phrase(loc_id, lang, sentence)
        conn.commit()
    

# for file_name in dircache.listdir('/usr/share/locale/fr/LC_MESSAGES'):
#     if file_name == "sharutils.mo":
#         continue
#     proj_name = file_name[:-3]
#     print "Processing project: ", proj_name
#     sys.stdout.flush()
#     proj = Project(proj_name)
#     print "  reading...",
#     sys.stdout.flush()
#     proj.read_selected(['fr', 'es', 'de', 'ru', 'sv', 'ja', 'pl', 'tr', 'it', 'nl', 'pt_BR'])
#     print "done."
#     print "  storing...",
#     sys.stdout.flush()
#     proj.store()
#     print "done."
#     sys.stdout.flush()


proj = Project(u"Słownik referencyjny KDE")
print "reading...",
sys.stdout.flush()
proj.read_file("kde.pot", "pl")
print "done."
print "storing...",
sys.stdout.flush()
proj.store()
print "done."
sys.stdout.flush()

con.cursor().execute ("create index loc_lang_idx on phrases (locationid, lang)")

#proj = Project("GConf2")
#proj.read_selected(['pl'])

#proj.output_phrases(('pl',''))

#p = Phrase('der konnte nicht typname verarbeitet warnung werden', DEHandler())
#print p.canonical()


#trans = gettext2.GNUTranslations(open('/usr/share/locale/pl/LC_MESSAGES/eog.mo', 'rb'))
#for k, v in trans.catalog.iteritems():
#phrase = "rock'n'roll'em"
#cursor.execute(u"insert into phrases (locationid, canonicalid, phrase) values (%s, %s, %s)", (3, 133, "rock'n'roll'em"))
#conn.commit()


conn.close()
