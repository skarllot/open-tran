#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#  Copyright (C) 2008 Jacek Śliwerski (rzyjontko)
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

import sys
from phrase import Phrase
from pysqlite2 import dbapi2 as sqlite
from common import LANGUAGES

iconn = sqlite.connect('/media/disk/data/nine-one.db')
icur = iconn.cursor()

sf = open('step2.sql')
sl = [x for x in sf.readlines() if not x.startswith('--')]
schema = reduce(lambda x, y: x + y, sl, '').split(';')
sf.close()

def define_schema(oconn, ocur):
    for stmt in schema:
        ocur.execute(stmt)
    oconn.commit()


def move_projects(oconn, ocur):
    icur.execute("""
SELECT id, name, url
FROM projects
""")
    for (id, name, url) in icur.fetchall():
        ocur.execute ("INSERT INTO projects (id, name, url) VALUES (?, ?, ?)", (id, name, url))
    oconn.commit()


def store_words(oconn, ocur, phraseid, words):
    cnt = 1
    last = words[0]
    for word in words[1:]:
        if word == last:
            cnt += 1
            continue
        ocur.execute(u"insert into words(word, phraseid, count) values (?, ?, ?)", \
                         (last, phraseid, cnt))
        last = word
        cnt = 1
    ocur.execute(u"insert into words(word, phraseid, count) values (?, ?, ?)", \
                     (last, phraseid, cnt))


def move_phrases(oconn, ocur, lang):
    cnt = 0
    phrase = ""

    icur.execute("""
SELECT id, phrase, lang, projectid, locationid
FROM phrases
WHERE lang = ?
ORDER BY phrase
""", (lang,))

    for (phraseid, nphrase, lang, projectid, lid) in icur.fetchall():
        if cnt % 5000 == 0:
            print ".",
            sys.stdout.flush()
        cnt += 1
        if phrase != nphrase:
            phrase = nphrase
            nphraseid = phraseid
            p = Phrase(nphrase, lang[:2])
            len = p.length()
            if len < 1:
                continue
            ocur.execute("INSERT INTO phrases (id, phrase, length) VALUES (?, ?, ?)", (nphraseid, nphrase, len))
            store_words(oconn, ocur, nphraseid, p.canonical_list())
        ocur.execute("INSERT INTO tlocations (projectid, phraseid, lang) VALUES (?, ?, ?)", (projectid, nphraseid, lang))
    oconn.commit()



for lang in sorted(LANGUAGES):
    if lang < 'ne':
        continue
    oconn = sqlite.connect('/media/disk/data/nine-' + lang + '.db')
    ocur = oconn.cursor()
    print "Moving %s phrases..." % lang,
    sys.stdout.flush()
    define_schema(oconn, ocur)
    move_projects(oconn, ocur)
    move_phrases(oconn, ocur, lang)
    print "done."
    sys.stdout.flush()
    ocur.close()
    oconn.close()

icur.close()
iconn.close()

