#!/usr/bin/python2.4
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

from translate.storage import factory
from phrase import Phrase
from pysqlite2 import dbapi2 as sqlite

import dircache, sys, os


def log(text, nonline=False):
    if nonline:
        print text,
    else:
        print text
    sys.stdout.flush()


def get_subdirs(dir):
    for r, dirs, files in os.walk(dir):
        if '.svn' in dirs:
            dirs.remove('.svn')
        return dirs


class Importer(object):
    def __init__(self, conn, parser_class):
        self.conn = conn
        self.parser_class = parser_class
    

    def store_phrase(self, lid, sentence, lang):
        phrase = Phrase(sentence, lang)
        if phrase.length() == 0:
            return
        self.cursor.execute(u"insert into phrases(locationid, lang, phrase) values (?, ?, ?)", \
                            (lid, lang, sentence))
        self.cursor.execute(u"insert into canonical(locationid, lang, phrase) values (?, ?, ?)", \
                            (lid, lang, phrase.canonical ()))


    def store_phrases(self, project, phrases):
        for source, ls in phrases.iteritems():
            if len(source) < 2:
                continue
            self.cursor.execute(u"insert into locations (project) values (?)", (project,))
            self.cursor.execute("select max (rowid) from locations")
            lid = self.cursor.fetchone()[0]
            self.store_phrase(lid, source, "C")
            for lang, target in ls.iteritems():
                self.store_phrase(lid, target, lang)


    def load_file(self, phrases, fname, lang):
        fname = fname.replace('/fr/', '/' + lang + '/', 1)
        store = self.parser_class.parsefile(fname)
        mlang = lang.replace('@', '_').lower()
        for unit in store.units:
            if len(str(unit.target)) > 0:
                l = phrases.setdefault(str(unit.source), {})
                l[mlang] = str(unit.target)
        return len(store.units)


    def store_file(self, project, fname):
        phrases = {}
        for lang in self.langs:
            log("  + %s..." % lang, True)
            try:
                cnt = self.load_file(phrases, fname, lang)
                log("ok (%d)" % cnt)
            except:
                log("failed.")
        log("  phrases: %d" % len(phrases))
        self.store_phrases(project, phrases)
        

    def run(self, dir):
        self.langs = get_subdirs(dir)
        for root, dirs, files in os.walk(os.path.join(dir, 'fr')):
            for f in files:
                if self.is_resource(f):
                    log("Importing %s..." % f)
                    self.cursor = self.conn.cursor()
                    self.store_file(self.project_name(f, root), os.path.join(root, f))
            if '.svn' in dirs:
                dirs.remove('.svn')


    def load_project_file(self, phrases, project, project_file):
        store = self.parser_class.parsefile(project_file)
        lang = project[:-3].replace('@', '_').lower()
        for unit in store.units:
            if len(str(unit.target)) > 0:
                l = phrases.setdefault(str(unit.source), {})
                l[lang] = str(unit.target)
        return len(store.units)


    def run_projects(self, dir):
        for proj in get_subdirs(dir):
            log("Importing %s..." % proj)
            self.cursor = self.conn.cursor()
            phrases = {}
            proj_file_name = os.path.join(dir, proj)
            for lang in os.listdir(proj_file_name):
                if not self.is_resource(lang):
                    continue
                log("  + %s..." % lang, True)
                try:
                    cnt = self.load_project_file(phrases, proj, os.path.join(proj_file_name, lang))
                    log("ok (%d)" % cnt)
                except:
                    log("failed.")
            log("  phrases: %d" % len(phrases))
            self.store_phrases(self.project_name(proj), phrases)


class KDE_Importer(Importer):
    def project_name(self, fname, root):
        return "KDE " + fname[:-3]
    
    def is_resource(self, fname):
        return fname.endswith('.po')
    
    def run(self):
        Importer.run(self, '/home/sliwers/kde-l10n')



class Mozilla_Importer(Importer):
    def get_idx(self, fname):
        if not hasattr(self, 'index'):
            self.index = fname.index('/fr/') + 4
        return self.index
    
    def project_name(self, fname, root):
        root = root[self.get_idx(root):]
        idx = root.find('/')
        if idx > 0:
            root = root[:idx]
        fname = fname[:fname.index('.')]
        return "Mozilla " + root + " " + fname
    
    def is_resource(self, fname):
        return fname.endswith('.dtd.po') or fname.endswith('.properties.po')
    
    def run(self):
        Importer.run(self, '/home/sliwers/mozilla-po')


class Gnome_Importer(Importer):
    def project_name(self, proj):
        return "Gnome " + proj
    
    def is_resource(self, fname):
        return fname.endswith('.po')
    
    def run(self):
        Importer.run_projects(self, '/home/sliwers/gnome-po')


cls = factory.getclass("kde.po")
conn = sqlite.connect('../data/seventh-i.db')
cursor = conn.cursor()
log("Dropping index...", True)
cursor.execute("drop index if exists loc_lang_idx")
log("done.")

ki = KDE_Importer(conn, cls)
ki.run()
mi = Mozilla_Importer(conn, cls)
mi.run()
gi = Gnome_Importer(conn, cls)
gi.run()

log("Creating index...", True)
cursor.execute("create index loc_lang_idx on phrases (locationid, lang)")
log("done.")
conn.close()
