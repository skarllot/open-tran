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

class Suggestion:
    def __init__ (self):
        self.count = 0
        self.value = 2000000000

    def set_value (self, value):
        self.count += 1
        if self.value > value:
            self.value = value

    def compare (self, sug):
        ret = (self.value > sug.value) - (self.value < sug.value)
        if ret != 0:
            return ret
        return (self.count < sug.count) - (self.count > sug.count)
    

class TranDB:
    def __init__ (self, srclang):
        self.db = '../data/seventh.db'
        self.srclang = srclang
        self.storage = tran.storage_create (srclang)
        tran.storage_read (self.storage, self.db)

    def __del__ (self):
        tran.storage_destroy (self.storage)
    
    def suggest (self, text, dstlang):
        sys.stdout.flush()
        suggs = tran.storage_suggest (self.storage, text)
        result = {}
        conn = sqlite.connect (self.db)
        cursor = conn.cursor ()
        for i in range (tran.suggestion_get_count (suggs)):
            idx = tran.suggestion_get_id (suggs, i)
            cursor.execute ("""
SELECT p.phrase, l.project
FROM phrases p JOIN locations l ON p.locationid = l.id
WHERE p.locationid = ? AND p.lang = ?""",
                            (idx, dstlang))
            rows = cursor.fetchall ()
            if len (rows):
                sug = Suggestion()
                sug.text = rows[0][0]
                sug.project = rows[0][1]
                sug = result.setdefault (sug.text, sug)
                sug.set_value (tran.suggestion_get_value (suggs, i))
        cursor.close ()
        tran.suggestion_destroy (suggs)
        result = result.values ()
        result.sort (lambda s1, s2: s1.compare (s2))
        return result
