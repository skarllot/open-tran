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


datadir = sys.argv[1] + '/../data'


langs = sorted(LANGUAGES)
str = "'" + langs[0] + "'"
for l in langs[1:]:
    str += ", '" + l + "'"

conn = sqlite.connect(datadir + '/ten.db')
cur = conn.cursor()

#cur.execute("DELETE FROM phrases WHERE lang NOT IN (" + str + ");")
#conn.commit()

projs = {}

cur.execute("""
SELECT substr(name, 1, 1), min(id), max(id)
FROM projects
GROUP BY substr(name, 1, 1)
""")
for (proj, min, max) in cur.fetchall():
    projs[proj] = (min, max)

for (proj, boundaries) in projs.items():
    cur.execute("""
SELECT count(*), count(distinct lang)
FROM phrases
WHERE projectid BETWEEN %d AND %d""" % boundaries)
    (cnt, lcnt) = cur.fetchone()
    print proj, cnt, lcnt
    cur.execute("""
SELECT count(*)
FROM phrases
WHERE lang = 'en'
  AND projectid BETWEEN %d AND %d""" % boundaries)
    (cnt,) = cur.fetchone()
    print proj, cnt


cur.execute("""
SELECT lang, count(*)
FROM phrases
GROUP BY lang""")
for (lang, cnt) in cur.fetchall():
    print (u'<tr><td>%s</td><td><a href="http://%s.open-tran.eu">%s</a></td><td align="right">%d</td></tr>' % (lang, lang, LANGUAGES[lang], cnt)).encode('utf-8')

cur.close()
conn.close()

