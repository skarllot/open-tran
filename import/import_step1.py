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

import dircache, sys, os, gc


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
    if shortlist:
        return shortlist
    return get_subdirs(dir)


class GlobalId(object):
    _id = 0
    
    @staticmethod
    def next():
        GlobalId._id += 1
        return GlobalId._id


class ImporterProject(object):
    lang_dict = {
        'as_in' : 'as',
        'be_by' : 'be',
        'fy_nl' : 'fy',
        'ga_ie' : 'ga',
        'gl_es' : 'gl',
        'hi_in' : 'hi',
        'hy_am' : 'hy',
        'ml_in' : 'ml',
        'mr_in' : 'mr',
        'nb_no' : 'nb',
        'nds_de' : 'nds',
        'nn_no' : 'nn',
        'ns' : 'nso',
        'or_in' : 'or',
        'sr_latin' : 'sr_latn',
        'sv_se' : 'sv',
        'sw_tz' : 'sw',
        'te_in' : 'te',
        'ven' : 've'
        }
        
    
    def __init__(self, cursor, project_id):
        self.phrase_ids = {}
        self.cursor = cursor
        self.project_id = project_id


    def __store_phrase(self, pid, lid, sentence, flags, lang):
        phrase = Phrase(sentence, lang[:2])
        length = phrase.length()
        if length == 0 or len(sentence) < 2 or length > 10:
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
""", (pid, lid, lang, length, sentence.decode('utf-8'), flags))


    def __lang_hygiene(self, lang):
        lang = lang.replace('@', '_').lower()
        if lang[:2] == lang[3:].lower():
            return lang[:2]
        lang = lang.replace('-', '_')
        lang = lang.replace('ooo_build_', '')
        if lang in ImporterProject.lang_dict:
            lang = ImporterProject.lang_dict[lang]
        return lang


    def load_file(self, fname, lang):
        store = factory.getclass('a.po').parsefile(fname)
        mlang = self.__lang_hygiene(lang)
        for unit in store.units:
            src = unit.source.encode('utf-8')
            dst = unit.target.encode('utf-8')
            key = (src, '::'.join(unit.getlocations())
                   + '::::' + unit.getcontext())
            if len(src) > 0:
                if key in self.phrase_ids:
                    pid = self.phrase_ids[key]
                else:
                    pid = GlobalId.next()
                    self.__store_phrase(self.project_id, pid, src, 0, "en")
                    self.phrase_ids[key] = pid
                self.__store_phrase(self.project_id, pid,
                                    dst, unit.isfuzzy(), lang)
        return len(store.units)


    def load_lang_file(self, fname, lang):
        fname = fname.replace('/fr/', '/' + lang + '/', 1)
        fname = fname.replace('_fr.po', '_' + lang + '.po', 1)
        fname = fname.replace('.fr.po', '.' + lang + '.po', 1)
        return self.load_file(fname, lang)




class Importer(object):
    global_pid = 0

    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()
    

    def store_file(self, pid, fname):
        ip = ImporterProject(self.cursor, pid)
        for lang in self.langs:
            log("  + %s..." % lang, True)
            try:
                cnt = ip.load_lang_file(fname, lang)
                log("ok (%d)" % cnt)
            except IOError:
                log("failed.")
        self.conn.commit()
        

    def run_langs(self, dir):
        self.langs = get_lsubdirs(dir)
        for root, dirs, files in os.walk(os.path.join(dir, 'fr')):
            for f in files:
                if self.is_resource(f):
                    rel = root[len(dir) + 1:]
                    name = self.get_path(rel, f)
                    log("Importing %s..." % f)
                    pid = self.store_project(name)
                    self.store_file(pid, os.path.join(root, f))
                    gc.collect()
            if '.svn' in dirs:
                dirs.remove('.svn')


    def run_project(self, directory, proj):
        log("Importing %s..." % proj)
        self.cursor = self.conn.cursor()
        proj_file_name = os.path.join(directory, proj)
        name = self.get_path(proj_file_name, proj)
        pid = self.store_project(name)
        ip = ImporterProject(self.cursor, pid)
        for lang in os.listdir(proj_file_name):
            if not self.is_resource(lang):
                continue
            log("  + %s..." % lang, True)
            try:
                fname = os.path.join(proj_file_name, lang)
                lang = lang[:-3].replace('@', '_').lower()
                cnt = ip.load_file(fname, lang)
                log("ok (%d)" % cnt)
            except:
                log("failed.")
        gc.collect()
        

    def run_projects(self, dir):
        for proj in get_subdirs(dir):
            self.run_project(dir, proj)
            gc.collect()


    def get_path(self, dir, name):
        if name.endswith(".fr.po"):
            name = name[:-6]
        if name.endswith(".po"):
            name = name[:-3]
        return self.getprefix() + "/" + name
        

    def store_project(self, name):
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
        if shortlist:
            return fname in map(lambda x: x + '.po', shortlist)
        return fname.endswith('.po')
    
    def get_language(self, project):
        return 
    
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
            items[en] = { "fy" : (fy, 0) }
        pid = Importer.store_project(self, "F/")
        self.store_phrases(pid, items)


        
class DI_Importer(Importer):
    def getprefix(self):
        return "D"
    
    def is_resource(self, fname):
        if shortlist:
            return fname in shortlist
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
        if shortlist:
            return fname in map(lambda x: x + '.po', shortlist)
        return fname.endswith('.po')

    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.run_projects(self, path)


class Inkscape_Importer(Importer):
    def getprefix(self):
        return "I"

    def is_resource(self, fname):
        if shortlist:
            return fname in map(lambda x: x + '.po', shortlist)
        return fname.endswith('.po')

    def get_language(self, project):
        return project[:-3].replace('@', '_').lower()
    
    def run(self, path):
        Importer.run_project(self, path, '')



class OO_Importer(Importer):
    def getprefix(self):
        return "O"

    def get_path(self, dir, name):
        dir = dir[3:]
        idx = dir.find('/')
        if idx >= 0:
            dir = dir[:idx]
        return self.getprefix() + "/" + dir + "/" + name[:-3]
    
    def is_resource(self, fname):
        return fname.endswith('.po')
    
    def run(self, path):
        Importer.run_langs(self, path)



shortlist = None #['fy', 'fy-NL']
root = sys.argv[1]
importers = {
    DI_Importer : '/debian-installer',
    FY_Importer : '/fy/kompjtr2.txt',
    Gnome_Importer : '/gnome-po',
    Inkscape_Importer : '/inkscape',
    KDE_Importer : '/l10n-kde4',
    Suse_Importer : '/suse-i18n',
    Xfce_Importer : '/xfce',
    Mozilla_Importer : '/mozilla-po',
    OO_Importer : '/oo-po'
    }

sf = open(sys.argv[1] + '/../import/step1.sql')
schema = sf.read()
sf.close()

conn = sqlite.connect(sys.argv[1] + '/../data/ten.db')
cursor = conn.cursor()
cursor.executescript(schema)
conn.commit()

mo = len(sys.argv) > 2 and sys.argv[2] == 'mo'

from traceback import print_exc

for icls, p in importers.iteritems():
    if mo and icls not in (Mozilla_Importer, OO_Importer):
        continue
    if not mo and icls in (Mozilla_Importer, OO_Importer):
        continue
    try:
        i = icls(conn)
        i.run(root + p)
        conn.commit()
    except Exception, inst:
        print_exc()
        sys.stderr.write('%s failed: %s\n' % (p, str(inst)))

conn.close()
