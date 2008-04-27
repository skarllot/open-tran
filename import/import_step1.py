#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#  Copyright (C) 2007, 2008 Jacek Śliwerski (rzyjontko)
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
    if debug:
        return ["pl", 'de']
    for r, dirs, files in os.walk(dir):
        if '.svn' in dirs:
            dirs.remove('.svn')
        return dirs


class Importer(object):
    global_pid = 0
    
    def __init__(self, conn, parser_class):
        Importer.global_pid += 1
        self.projectid = Importer.global_pid
        self.location = 0
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.parser_class = parser_class
    

    def store_phrase(self, pid, lid, sentence, lang):
        phrase = Phrase(sentence, lang[:2])
        length = phrase.length()
        if length == 0:
            return
        self.cursor.execute(u"insert into phrases(projectid, locationid, lang, length, phrase) values (?, ?, ?, ?, ?)", \
                            (pid, lid, lang, length, sentence))


    def store_phrases(self, pid, phrases):
        for source, ls in phrases.iteritems():
            if len(source) < 2:
                continue
            self.location += 1
            self.store_phrase(pid, self.location, source, "en")
            for lang, target in ls.iteritems():
                self.store_phrase(pid, self.location, target, lang)
        self.conn.commit()


    def load_file(self, phrases, fname, lang):
        fname = fname.replace('/fr/', '/' + lang + '/', 1)
        fname = fname.replace('_fr.po', '_' + lang + '.po', 1)
        store = self.parser_class.parsefile(fname)
        mlang = lang.replace('@', '_').lower()
        for unit in store.units:
            src = unit.source.encode('utf-8')
            dst = unit.target.encode('utf-8')
            if len(src) > 0:
                l = phrases.setdefault(src, {})
                l[mlang] = dst
        return len(store.units)


    def store_file(self, pid, fname):
        phrases = {}
        for lang in self.langs:
            log("  + %s..." % lang, True)
            try:
                cnt = self.load_file(phrases, fname, lang)
                log("ok (%d)" % cnt)
            except:
                log("failed.")
        log("  phrases: %d" % len(phrases))
        self.store_phrases(pid, phrases)
        

    def run_langs(self, dir):
        self.langs = get_subdirs(dir)
        for root, dirs, files in os.walk(os.path.join(dir, 'fr')):
            for f in files:
                if self.is_resource(f):
                    log("Importing %s..." % f)
                    self.store_file(self.projectid, os.path.join(root, f))
            if '.svn' in dirs:
                dirs.remove('.svn')


    def load_project_file(self, phrases, project, project_file):
        store = self.parser_class.parsefile(project_file)
        lang = self.get_language(project)
        for unit in store.units:
            src = unit.source.encode('utf-8')
            dst = unit.target.encode('utf-8')
            if len(src) > 0:
                l = phrases.setdefault(src, {})
                l[lang] = dst
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
                    cnt = self.load_project_file(phrases, lang, os.path.join(proj_file_name, lang))
                    log("ok (%d)" % cnt)
                except:
                    log("failed.")
            log("  phrases: %d" % len(phrases))
            self.store_phrases(self.projectid, phrases)


    def store_project(self):
        self.cursor.execute("insert into projects (id, name, url) values (?, ?, ?)",
                            (self.projectid, self.project_name(), self.project_url()))


class KDE_Importer(Importer):
    def project_name(self):
        return "KDE"

    def project_url(self):
        return "http://www.kde.org"
    
    def is_resource(self, fname):
        return fname.endswith('.po')
    
    def run(self, path):
        Importer.store_project(self)
        Importer.run_langs(self, path)



class Mozilla_Importer(Importer):
    def project_name(self):
        return "Mozilla"

    def project_url(self):
        return "http://www.mozilla.org"
    
    def is_resource(self, fname):
        return fname.endswith('.dtd.po') or fname.endswith('.properties.po')
    
    def run(self, path):
        Importer.store_project(self)
        Importer.run_langs(self, path)



class Gnome_Importer(Importer):
    def project_name(self):
        return "Gnome"

    def project_url(self):
        return "http://www.gnome.org"
    
    def is_resource(self, fname):
        if debug:
            return fname == 'pl.po' or fname == 'de.po'
        return fname.endswith('.po') and not fname.startswith('en')
    
    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.store_project(self)
        Importer.run_projects(self, path)



class FY_Importer(Importer):
    def project_name(self):
        return "FY"
    
    def project_url(self):
        return "http://members.chello.nl/~s.hiemstra/kompjtr.htm"
    
    def run(self, path):
        items = {}
        f = open(path)
        self.cursor = self.conn.cursor()
        for line in f:
            en, fy = line.rstrip().split(" | ")
            items[en] = { "fy" : fy }
        Importer.store_project(self)
        self.store_phrases(self.projectid, items)

        
class DI_Importer(Importer):
    def project_name(self):
        return "DI"

    def project_url(self):
        return "http://www.debian.org/devel/debian-installer/"
    
    def is_resource(self, fname):
        return fname.endswith('.po')
    
    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.store_project(self)
        Importer.run_langs(self, path)


debug = 0
root = '/home/sliwers/projekty/open-tran-data'
pocls = factory.getclass("kde.po")
conn = sqlite.connect('../data/nine-one.db')
cursor = conn.cursor()
importers = {
    DI_Importer(conn, pocls) : '/debian-installer',
    FY_Importer(conn, pocls) : '/fy/kompjtr2.txt',
    KDE_Importer(conn, pocls) : '/kde-l10n',
    Mozilla_Importer(conn, pocls) : '/mozilla-po',
    Gnome_Importer(conn, pocls) : '/gnome-po'
    }

for i, p in importers.iteritems():
    i.run(root + p)

conn.close()
