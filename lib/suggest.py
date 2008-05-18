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

from pysqlite2 import dbapi2 as sqlite
from xml.sax.saxutils import escape, quoteattr
from phrase import Phrase

PROJS = {
    'D': 'Debian Installer',
    'F': 'FY',
    'G': 'GNOME',
    'K': 'KDE',
    'M': 'Mozilla',
    'S': 'openSUSE',
    'X': 'XFCE'
    }

class Project:
    pass

class Suggestion:
    def __init__ (self, text, value):
        self.count = 0
        self.value = value
        self.text = text
        self.projects = {}

    def append_project(self, project, orig):
        x = Project()
        x.name = project
        x.orig_phrase = orig
        x.count = 0
        x = self.projects.setdefault(orig, x)
        x.count += 1
        self.count += 1
    
    def compare (self, sug):
        ret = (self.value > sug.value) - (self.value < sug.value)
        if ret != 0:
            return ret
        ret = (self.count < sug.count) - (self.count > sug.count)
        if ret != 0:
            return ret
        return cmp(self.text, sug.text)

    def finish(self):
        self.projects = self.projects.values()
        self.projects.sort(key=lambda x: x.count, reverse=True)
    

class TranDB:
    def __init__(self):
        self.db = '../data/nine-'
    
    def renumerate(self, suggs):
        if len(suggs) == 0:
            return suggs
        if len(suggs) == 1:
            suggs[0].value = 1
            return suggs
        value = 1
        prev = suggs[0]
        for next in suggs[1:]:
            oldvalue = value
            if prev.value != next.value:
                value += 1
            prev.value = oldvalue
            prev = next
        next.value = value
        return suggs

    def qmarks_string(self, words):
        result = "(?"
        for w in words[1:]:
            result += ", ?"
        return result + ")"

    def suggest (self, text, dstlang):
        '''
Is equivalent to calling suggest2(text, "en", dstlang)
'''
        return self.suggest2(text, "en", dstlang)

    def suggest2 (self, text, srclang, dstlang):
        '''
Translates text from srclang to dstlang.  Each language code must be one
of those displayed in the drop-down list in the search form.

Server sends back a result in the following form:
 * count: integer
 * text: string
 * value: integer
 * projects: list
   * count: integer
   * name: string
   * orig_phrase: string

Identical translations are grouped together as one suggestion - the 'count'
tells, how many of them there are.  The value indicates, how good the result
is - the lower, the better.  And the list contains tripples: name of the
project, phrase and count.  The sum of counts in the list of projects equals
the count stored in the suggestion object.

As an example consider a call: suggest2("save as", "en", "pl").  The server would
send a list of elements containing the following one:
 * count: 12
 * text: Zapisz jako
 * value: 1
 * projects[0]:
   * name: GNOME
   * orig_phrase: Save As
   * count: 9
 * projects[0]:
   * name: GNOME
   * orig_phrase: Save as
   * count: 1
 * projects[2]:
   * name: KDE
   * orig_phrase: Save File As
   * count: 1
 * projects[3]:
   * name: Mozilla
   * orig_phrase: Save
   * count: 1
'''
        result = {}
        phrase = Phrase(text, srclang, False)
        if phrase.length() < 1:
            return result
        words = phrase.canonical_list()
        qmarks = self.qmarks_string(words)
        conn = sqlite.connect(self.db + srclang + ".db")
        cursor = conn.cursor ()
        cursor.execute ("""
SELECT p.phrase, l.locationid, val.value
FROM phrases p
JOIN locations l ON p.id = l.phraseid
JOIN (
     SELECT p.id AS id, MAX(p.length) - SUM(wp.count) - COUNT(*) AS value
     FROM words w JOIN wp ON w.id = wp.wordid
     JOIN phrases p ON wp.phraseid = p.id
     WHERE word IN %s
     GROUP BY p.id
     ORDER BY value
     LIMIT 500
) val ON l.phraseid = val.id
""" % qmarks, tuple(words))
        rows = cursor.fetchall()
        for (orig, lid, value) in rows:
            dconn = sqlite.connect(self.db + dstlang + ".db")
            dcur = dconn.cursor()
            dcur.execute("""
SELECT DISTINCT phrase, project
FROM phrases p JOIN locations l ON p.id = l.phraseid
WHERE locationid = ?""", (lid,))
            for (trans, project) in dcur.fetchall():
                sug = Suggestion(trans, value)
                res = result.setdefault(sug.text, sug)
                res.append_project(PROJS[project], orig)
            dcur.close()
            dconn.close()
        cursor.close ()
        conn.close()
        result = result.values()
        result.sort (lambda s1, s2: s1.compare (s2))
        for s in result: s.finish()
        return self.renumerate(result[:50])

