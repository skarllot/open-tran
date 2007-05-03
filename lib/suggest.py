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

import tran, sys
from pysqlite2 import dbapi2 as sqlite
from xml.sax.saxutils import escape, quoteattr

class Project:
    pass

class Suggestion:
    def __init__ (self, text):
        self.count = 0
        self.value = 2000000000
        self.text = text
        self.projects = []

    def set_value (self, value):
        self.count += 1
        if self.value > value:
            self.value = value

    def append_project(self, project, orig_phrase):
        x = Project()
        x.path = project
        x.orig_phrase = orig_phrase
        self.projects.append(x)
    
    def compare (self, sug):
        ret = (self.value > sug.value) - (self.value < sug.value)
        if ret != 0:
            return ret
        ret = (self.count < sug.count) - (self.count > sug.count)
        if ret != 0:
            return ret
        return cmp(self.text, sug.text)
    

class TranDB:
    def __init__ (self, srclang):
        self.db = '../data/seventh.db'
        self.srclang = srclang
        self.storage = tran.storage_create (srclang)
        tran.storage_read (self.storage, self.db)

    def __del__ (self):
        tran.storage_destroy (self.storage)
    
    def renumerate(self, suggs):
        if len(suggs) < 2:
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

    def suggest (self, text, dstlang):
        sys.stdout.flush()
        suggs = tran.storage_suggest (self.storage, text)
        result = {}
        conn = sqlite.connect (self.db)
        cursor = conn.cursor ()
        for i in range (tran.suggestion_get_count (suggs)):
#            try:
                pid = tran.suggestion_get_project_id (suggs, i)
                lid = tran.suggestion_get_location_id (suggs, i)
                cursor.execute ("""
SELECT t.phrase, o.phrase, p.path
FROM phrases t
JOIN phrases o  ON o.locationid = t.locationid
               AND o.projectid = t.projectid
JOIN projects p ON o.projectid = p.id
WHERE o.locationid = ?
  AND o.projectid = ?
  AND o.lang = ?
  AND t.lang = ?
""",
                                (lid, pid, self.srclang, dstlang))
                rows = cursor.fetchall ()
                if len (rows):
                    sug = Suggestion(rows[0][0])
                    res = result.setdefault (sug.text, sug)
                    res.append_project(rows[0][2], rows[0][1])
                    res.set_value (tran.suggestion_get_value (suggs, i))
#            except:
#                pass
        cursor.close ()
        tran.suggestion_destroy (suggs)
        result = result.values ()
        result.sort (lambda s1, s2: s1.compare (s2))
        return self.renumerate(result)
