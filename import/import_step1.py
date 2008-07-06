#!/usr/bin/python
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
    for r, dirs, files in os.walk(dir):
        if '.svn' in dirs:
            dirs.remove('.svn')
        return dirs

def get_lsubdirs(dir):
    if debug:
        return ["de", "pl"]
    return get_subdirs(dir)


class Importer(object):
    global_pid = 0
    global_loc = 0
    lang_dict = {
        'fy_nl' : 'fy',
        'ga_ie' : 'ga',
        'hy_am' : 'hy',
        'nb_no' : 'nb',
        'nds_de' : 'nds',
        'nn_no' : 'nn',
        'sv_se' : 'sv'
        }
        
    
    def __init__(self, conn, parser_class):
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.parser_class = parser_class
    

    def lang_hygiene(self, lang):
        if lang[:2] == lang[3:].lower():
            return lang[:2]
        lang = lang.replace('-', '_')
        if lang in Importer.lang_dict:
            lang = Importer.lang_dict[lang]
        return lang


    def store_phrase(self, pid, lid, sentence, flags, lang):
        phrase = Phrase(sentence, lang[:2])
        length = phrase.length()
        if length == 0:
            return
        if flags:
            flags = 1
        else:
            flags = 0
        self.cursor.execute(u"""
insert into phrases
    (projectid, locationid, lang, length, phrase, flags)
values
    (?, ?, ?, ?, ?, ?)
""", (pid, lid, lang, length, sentence, flags))


    def store_phrases(self, pid, phrases):
        for source, ls in phrases.iteritems():
            if len(source) < 2:
                continue
            Importer.global_loc += 1
            self.store_phrase(pid, Importer.global_loc, source, 0, "en")
            for lang, target in ls.iteritems():
                self.store_phrase(pid, Importer.global_loc, target[0], target[1], lang)
        self.conn.commit()


    def load_file(self, phrases, fname, lang):
        fname = fname.replace('/fr/', '/' + lang + '/', 1)
        fname = fname.replace('_fr.po', '_' + lang + '.po', 1)
        fname = fname.replace('.fr.po', '.' + lang + '.po', 1)
        store = self.parser_class.parsefile(fname)
        mlang = lang.replace('@', '_').lower()
        mlang = self.lang_hygiene(mlang)
        for unit in store.units:
            src = unit.source.encode('utf-8')
            dst = unit.target.encode('utf-8')
            if len(src) > 0:
                l = phrases.setdefault(src, {})
                l[mlang] = (dst, unit.isfuzzy())
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
        self.langs = get_lsubdirs(dir)
        for root, dirs, files in os.walk(os.path.join(dir, 'fr')):
            for f in files:
                if self.is_resource(f):
                    log("Importing %s..." % f)
                    pid = self.store_project(f)
                    self.store_file(pid, os.path.join(root, f))
            if '.svn' in dirs:
                dirs.remove('.svn')


    def load_project_file(self, phrases, project, project_file):
        store = self.parser_class.parsefile(project_file)
        lang = self.get_language(project)
        lang = self.lang_hygiene(lang)
        for unit in store.units:
            src = unit.source.encode('utf-8')
            dst = unit.target.encode('utf-8')
            if len(src) > 0:
                l = phrases.setdefault(src, {})
                l[lang] = (dst, unit.isfuzzy())
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
            pid = self.store_project(os.path.basename(proj_file_name))
            self.store_phrases(pid, phrases)


    def store_project(self, name):
        if name.endswith(".fr.po"):
            name = name[:-6]
        if name.endswith(".po"):
            name = name[:-3]
        name = self.getprefix() + "/" + name
        Importer.global_pid += 1
        self.cursor.execute("insert into projects (id, name) values (?, ?)",
                            (Importer.global_pid, name))
        return Importer.global_pid



class KDE_Importer(Importer):
    def getprefix(self):
        return "K"

    def is_resource(self, fname):
        return fname.endswith('.po')
    
    def run(self, path):
        Importer.run_langs(self, path)



class Mozilla_Importer(Importer):
    def getprefix(self):
        return "M"

    def is_resource(self, fname):
        return fname.endswith('.dtd.po') or fname.endswith('.properties.po')
    
    def run(self, path):
        Importer.run_langs(self, path)



class Gnome_Importer(Importer):
    def getprefix(self):
        return "G"
    
    def is_resource(self, fname):
        if debug:
            return fname == 'pl.po' or fname == 'de.po'
        return fname.endswith('.po')
    
    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.run_projects(self, path)



class FY_Importer(Importer):
    def getprefix(self):
        return "F"
    
    def run(self, path):
        items = {}
        f = open(path)
        self.cursor = self.conn.cursor()
        for line in f:
            en, fy = line.rstrip().split(" | ")
            items[en] = { "fy" : fy }
        pid = Importer.store_project(self, "")
        self.store_phrases(pid, items)


        
class DI_Importer(Importer):
    def getprefix(self):
        return "D"
    
    def is_resource(self, fname):
        if debug:
            return fname == 'pl.po' or fname == 'de.po'
        return fname.endswith('.po')
    
    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.run_projects(self, path)



class Suse_Importer(Importer):
    def getprefix(self):
        return "S"
    
    def is_resource(self, fname):
        return fname.endswith('.po')

    def run(self, path):
        Importer.run_langs(self, path + '/yast')
        Importer.run_langs(self, path + '/lcn')



class Xfce_Importer(Importer):
    def getprefix(self):
        return "X"

    def is_resource(self, fname):
        if debug:
            return fname == 'pl.po' or fname == 'de.po'
        return fname.endswith('.po')

    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.run_projects(self, path)


debug = 0
root = '/home/sliwers/projekty/open-tran-data'
pocls = factory.getclass("kde.po")
conn = sqlite.connect('../data/ten.db')
cursor = conn.cursor()
importers = {
    DI_Importer(conn, pocls) : '/debian-installer',
    FY_Importer(conn, pocls) : '/fy/kompjtr2.txt',
    KDE_Importer(conn, pocls) : '/l10n-kde4',
    Mozilla_Importer(conn, pocls) : '/mozilla-po',
    Gnome_Importer(conn, pocls) : '/gnome-po',
    Suse_Importer(conn, pocls) : '/suse-i18n',
    Xfce_Importer(conn, pocls) : '/xfce'
    }

sf = open('step1.sql')
schema = sf.read()
sf.close()
cursor.executescript(schema)
conn.commit()

for i, p in importers.iteritems():
    i.run(root + p)

log("Creating index...", True)
cursor.execute("CREATE INDEX idx ON phrases(lang);")
log("done.")
conn.commit()
conn.close()
