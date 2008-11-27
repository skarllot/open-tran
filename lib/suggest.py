#!/usr/bin/env python
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
import sys, os

PROJS = {
    'D': 'Debian Installer',
    'F': 'FY',
    'G': 'GNOME',
    'I': 'Inkscape',
    'K': 'KDE',
    'M': 'Mozilla',
    'O': 'OpenOffice.org',
    'S': 'SUSE',
    'X': 'XFCE'
    }

def sanitize_language(lang):
    lang = lang.lower()
    lang = lang.replace('-', '_')
    return lang

class TmpSug:
    def __init__(self, text, orig, project, value, flags):
        self.text = text
        self.orig = orig
        self.project = project
        self.value = value
        self.flags = flags

class Project:
    pass

class Suggestion:
    def __init__ (self, text, value):
        self.count = 0
        self.value = value
        self.text = text
        self.projects = {}

    def __proj_zip__(self):
        res = {}
        for p in self.projects:
            x = res.setdefault(p.name, p)
            if x != p:
                x.count += p.count
        res = res.values()
        return sorted(res, lambda a, b: b.count - a.count)
    
    def __str__(self):
        result = self.text + " ("
        for proj in self.__proj_zip__():
            if result[-1] != '(':
                result += " + "
            if proj.count > 1:
                result += "%d * " % proj.count
            result += proj.name
        result += ")"
        for proj in self.projects:
            result += "\n\t" + proj.name + ": " + proj.orig_phrase
            if proj.flags == 1:
                result += " ***fuzzy***"
        return result.encode('utf-8')
    
    def append_project(self, project, orig, value, flags):
        x = Project()
        x.name = PROJS[project[0]]
        x.path = project
        x.orig_phrase = orig
        x.count = 0
        x.flags = flags
        x = self.projects.setdefault(orig, x)
        x.count += 1
        self.count += 1
        if flags == 0 and self.value > value:
            self.value = value
    
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
    def __init__(self, dbpath):
        self.db = dbpath + '/ten-'
    
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


    def regroup(self, suggs):
        result = {}
        for sug in suggs:
            res = Suggestion(sug.text, sug.value)
            res = result.setdefault(sug.text.strip(), res)
            res.append_project(sug.project, sug.orig, sug.value, sug.flags)
        result = result.values()
        for s in result: s.finish()
        result.sort (lambda s1, s2: s1.compare (s2))
        return self.renumerate(result[:50])
        

    def qmarks_string(self, words):
        result = "(?"
        for w in words[1:]:
            result += ", ?"
        return result + ")"


    def get_translations(self, text, srclang, dstlang):
        srclang = sanitize_language(srclang)
        dstlang = sanitize_language(dstlang)
        result = []
        phrase = Phrase(text, srclang, False)
        if phrase.length() < 1:
            return result
        words = phrase.canonical_list()
        qmarks = self.qmarks_string(words)
        conn = sqlite.connect(self.db + srclang + ".db")
        cursor = conn.cursor ()
        cursor.execute ("""
ATTACH ? AS dest
""", (self.db + dstlang + '.db',))
        cursor.execute ("""
SELECT dst.phrase, src.phrase, dstl.project, dstl.flags, val.value
FROM phrases src
JOIN locations srcl ON src.id = srcl.phraseid
JOIN (
     SELECT p.id AS id, MAX(p.length) - SUM(wp.count) - COUNT(*) AS value
     FROM words w JOIN wp ON w.id = wp.wordid
     JOIN phrases p ON wp.phraseid = p.id
     WHERE word IN %s
     GROUP BY p.id
     ORDER BY value
     LIMIT 200
) val ON srcl.phraseid = val.id
JOIN dest.locations dstl ON srcl.locationid = dstl.locationid
JOIN dest.phrases dst ON dstl.phraseid = dst.id
ORDER BY dstl.flags, val.value
""" % qmarks, tuple(words))
        rows = cursor.fetchall()
        for (trans, orig, project, flags, value) in rows:
	    sug = TmpSug(trans, orig, project, value, flags)
	    result.append(sug)
        cursor.close ()
        conn.close()
        return result
        

    def suggest(self, text, dstlang):
        '''
Is equivalent to calling suggest2(text, "en", dstlang)
'''
        return self.suggest2(text, "en", dstlang)

    def suggest2(self, text, srclang, dstlang):
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
   * path: string
   * orig_phrase: string
   * flags: integer

Identical translations are grouped together as one suggestion - the 'count'
tells, how many of them there are.  The value indicates, how good the result
is - the lower, the better.  And the list contains quadruples: name of the
project name, original phrase, count and flags.  The sum of counts in the list
of projects equals the count stored in the suggestion object.  The flags are
currently only used to indicate if the translation is fuzzy (1) or not (0).

As an example consider a call: suggest2("save as", "en", "pl").  The server would
send a list of elements containing the following one:
 * count: 20
 * text: Zapisz jako...
 * value: 1
 * projects[0]:
   * name: GNOME
   * path: G/drgeo
   * orig_phrase: Save As...
   * count: 13
   * flags: 0
 * projects[1]:
   * name: GNOME
   * path: G/gxsnmp
   * orig_phrase: Save as...
   * count: 4
   * flags: 0
 * projects[2]:
   * name: SUSE
   * path: S/kpowersave
   * orig_phrase: Save As ...
   * count: 1
   * flags: 0
 * projects[3]:
   * name: KDE
   * path: K/koffice
   * orig_phrase: Save Document As
   * count: 1
   * flags: 0
 * projects[4]:
   * name: GNOME
   * path: G/gedit
   * orig_phrase: Save As…
   * count: 1
   * flags: 0
'''
        suggs = self.get_translations(text, srclang, dstlang)
        return self.regroup(suggs)


    def suggest3(self, text, srclang, dstlang, maxcount):
        '''
Is equivalent to calling suggest2(text, srclang, dstlang) and limiting
the number of returned records to maxcount.
'''
        return self.suggest2(text, srclang, dstlang)[:maxcount]


    def compare(self, text, lang):
        '''
Returns the same results as suggest, but grouped by the projects.
'''
        result = {}
        suggs = self.get_translations(text, "en", lang)
        for prefix, project in PROJS.iteritems():
            subres = self.regroup([s for s in suggs if s.project[0] == prefix])
            if len(subres) > 0:
                result[project] = subres
        return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: suggest.py phrase [LANG]"
        exit(0)
    lang = os.environ['LANG'].lower()
    lang = lang.split('.')[0]
    if lang[:2] == lang[3:]:
        lang = lang[:2]
    if len(sys.argv) > 2:
        lang = sys.argv[2]
    db = TranDB(os.path.expanduser('~/.open-tran'))
    i = 1
    for sug in db.suggest(sys.argv[1], lang):
        print "%2d: %s" % (i, sug)
        i += 1
    
