#!/usr/bin/python
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
from pysqlite2 import dbapi2 as sqlite
from common import LANGUAGES


for lang in sorted(LANGUAGES):
    conn = sqlite.connect('../data/nine-' + lang + '.db')
    cur = conn.cursor()
    print "Cleaning %s locations..." % lang,
    sys.stdout.flush()
    cur.execute("""
INSERT INTO locations (projectid, phraseid, lang, count)
SELECT projectid, phraseid, ?, count(*)
FROM tlocations
GROUP BY projectid, phraseid
""", (lang,))
    cur.execute("DROP TABLE tlocations")
    print "done."
    sys.stdout.flush()
    conn.commit()
    cur.close()
    conn.close()
