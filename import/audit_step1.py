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
from datetime import date

datadir = sys.argv[1] + '/../data'


class Project:
    def __init__(self, name, url, icon, branch, lic):
        self.name = name
        self.url = url
        self.icon = icon
        self.branch = branch
        self.lic = lic
        self.min = -1
        self.max = -1
        self.langs = 0
        self.total = 0
        self.eng = 0


projects = {
    'K': Project("KDE", "http://www.kde.org", "/images/kde-logo.png",
                 "trunk", '<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>(<a href="http://en.wikipedia.org/wiki/KDE#Licensing_issues" rel="nofollow">issues</a>)'),
    'M': Project("Mozilla", "http://www.mozilla.org",
                 "/images/mozilla-logo.png", "MOZILLA_1_8_BRANCH",
                 '<a href="http://www.mozilla.org/MPL/">MPL</a>/<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>/<a href="http://www.gnu.org/licenses/lgpl.html">LGPL</a> (<a href="http://en.wikipedia.org/wiki/Mozilla_Firefox#Licensing" rel="nofollow">issues</a>)'),
    'G': Project("GNOME", "http://www.gnome.org", "/images/gnome-logo.png",
                 "trunk", '<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>/<a href="http://www.gnu.org/licenses/lgpl.html">LGPL</a>'),
    'D': Project("Debian Installer",
                 "http://www.debian.org/devel/debian-installer/",
                 "/images/debian-logo.png", "level1",
                 '<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>'),
    'F': Project("Cor Jousma",
                 "http://members.chello.nl/~s.hiemstra/kompjtr.htm",
                 "/images/pompelyts.png", "",
                 '<a href="http://www.gnu.org/copyleft">Copyleft</a>'),
    'S': Project("openSUSE", "http://www.opensuse.org",
                 "/images/suse-logo.png", "trunk",
                 '<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>'),
    'X': Project("XFCE", "http://www.xfce.org", "/images/xfce-logo.png",
                 "trunk", '<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>/<a href="http://www.gnu.org/copyleft/lgpl.html">LGPL</a>'),
    'I': Project("Inkscape", "http://www.inkscape.org",
                 "/images/inkscape-logo.png", "trunk",
                 '<a href="http://www.gnu.org/copyleft/gpl.html">GPL</a>'),
    'O': Project("OpenOffice.org", "http://www.openoffice.org",
                 "/images/oo-logo.png", "",
                 '<a href="http://www.gnu.org/licenses/lgpl.html">LGPL</a>')
    }



conn = sqlite.connect(datadir + '/ten.db')
cur = conn.cursor()

cur.execute("CREATE INDEX idx ON phrases(projectid)")
conn.commit()

cur.execute("""
SELECT substr(name, 1, 1), min(id), max(id)
FROM projects
GROUP BY substr(name, 1, 1)
""")
for (proj, mn, mx) in cur.fetchall():
    projects[proj].min = mn
    projects[proj].max = mx

for proj in projects.values():
    cur.execute("""
SELECT count(*), count(distinct lang)
FROM phrases
WHERE projectid BETWEEN %d AND %d""" % (proj.min, proj.max))
    (cnt, lcnt) = cur.fetchone()
    proj.total = cnt
    proj.langs = lcnt
    cur.execute("""
SELECT count(*)
FROM phrases
WHERE lang = 'en'
  AND projectid BETWEEN %d AND %d""" % (proj.min, proj.max))
    (cnt,) = cur.fetchone()
    proj.eng = cnt

cur.close()
conn.close()

def pretty_int(s):
    return ",".join([str(a) for a in
                     [(s / 1000000) % 1000, (s / 1000) % 1000, s % 1000]
                     if a > 0])


print '''
<div class="ltr">
<h1>Projects</h1>
<p>
  Latest import was created from the sources updated on %s.
</p>
<table border="1">
  <tr>
    <th>Project</th>
    <th>Branch</th>
    <th>English Phrases</th>
    <th>Total Phrases</th>
    <th>Languages</th>
    <th>License</th>
  </tr>
''' % date.today().strftime('%B %d, %Y')

projs = sorted(projects.values(), key = lambda p: p.total, reverse = True)
for project in projs:
    if not project.total:
        continue
    print '<tr>'
    print '\t<td><a href="%s"><img src="%s" alt="%s"/> %s</a></td>' \
        % (project.url, project.icon, project.name, project.name)
    print '\t<td>%s</td>' % project.branch
    print '\t<td align="right">%s</td>' % pretty_int(project.eng)
    print '\t<td align="right">%s</td>' % pretty_int(project.total)
    print '\t<td align="right">%d</td>' % project.langs
    print '\t<td>%s</td>' % project.lic
    print '</tr>'

print '''
</table>
</div>
'''
