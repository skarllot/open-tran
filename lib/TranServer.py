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

from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ThreadingMixIn
from signal import signal, SIGPIPE, SIG_IGN
from suggest import TranDB
from translate.storage import factory
from tempfile import NamedTemporaryFile
from phrase import Phrase
from StringIO import StringIO

import email
import xmlrpclib
import urllib
import posixpath
import os


SUGGESTIONS_TXT = {
    'ca' : u'Possibles traduccions',
    'csb': u'Sugerowóny dolmaczënczi',
    'da' : u'Oversćttelsesforslag',
    'de' : u'Übersetzungsvorschläge',
    'es' : u'Sugerencias de traducción',
    'fi' : u'Käännös ehdotukset',
    'fr' : u'Traductions suggérées',
    'it' : u'Suggerimenti traduzione',
    'pl' : u'Sugestie tłumaczeń',
    'uk' : u'Запропоновані переклади'
    }

LANGUAGES = ['af','ar','az','be','bg','bn','br','bs','ca','cs','csb','cy','da','de','el','en_gb','eo','es','et','eu','fa','fi','fo','fr','fy','ga','gl','ha','he','hi','hr','hsb','hu','id','is','it','ja','ka','kk','km','ko','ku','lb','lo','lt','lv','mg','mi','mk','mn','ms','mt','nb','nds','ne','nl','nn','oc','pa','pl','pt','pt_br','ro','ru','rw','se','sk','sl','sq','sr','sr_latn','ss','sv','ta','te','tg','th','tr','tt','uk','uz','ven','vi','wa','xh','zh_cn','zh_hk','zh_tw','zu']

RTL_LANGUAGES = ['ar', 'fa', 'ha', 'he']


def _replace_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')



class renderer(object):
    def __init__(self):
        self.projects = []
    
    def clear(self):
        self.projects = []

    def feed(self, path):
        if self.may_render(path):
            self.projects.append(path)

    def render_icon(self, needplus):
        cnt = len(self.projects)
        if cnt == 0:
            return ""
        if needplus:
            result = " + "
        else:
            result = ""
        if cnt > 1:
            result += "%d&times;" % cnt
        return result + '<img src="%s" alt="%s"/>' % (self.icon_path, self.name)

    def render_links(self, lang):
        result = ""
        for project in self.projects:
            result += "%s / %s<br/>\n" % (self.render_link(project.path, lang), _replace_html(project.orig_phrase))
        return result


class gnome_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "GNOME"
        self.icon_path = "http://www.gnome.org/img/logo/foot-16.png"
    
    def may_render(self, project):
        return project.path[0] == 'G'

    def render_link(self, path, lang):
        path = path[2:]
        fname = os.path.basename(path)
        while len(path):
            path, rest = os.path.split(path)
        return '<a href="http://svn.gnome.org/svn/%s/trunk/po/%s.po">GNOME %s</a>' % (rest, lang, rest)
    

class kde_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "KDE"
        self.icon_path = "http://kde.org/favicon.ico"
        self.langs = { 'en_gb' : 'en_GB',
                       'pt_br' : 'pt_BR',
                       'sr_latn' : 'sr@Latn',
                       'zh_cn' : 'zh_CN',
                       'zh_hk' : 'zh_HK',
                       'zh_tw' : 'zh_TW' }

    def may_render(self, project):
        return project.path[0] == 'K'

    def render_link(self, path, lang):
        fname = os.path.basename(path)
        if lang in self.langs:
            lang = self.langs[lang]
        return '<a href="http://websvn.kde.org/branches/stable/l10n/%s/messages/%s?view=markup">KDE %s</a>' % (lang, path[2:], fname[:-3])


class mozilla_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "Mozilla"
        self.icon_path = "http://www.mozilla.org/images/mozilla-16.png"

    def may_render(self, project):
        return project.path[0] == 'M'

    def render_link(self, path, lang):
        path = path[2:]
        fname, ext = os.path.splitext(os.path.basename(path))
        while len(ext):
            fname, ext = os.path.splitext(fname)
        folder, rest = os.path.split(os.path.dirname(path))
        while len(folder):
            folder, rest = os.path.split(folder)
        return '<a href="http://www.mozilla.org/projects/l10n/">Mozilla %s %s</a>' % (rest, fname)


class Suggestion:
    def __init__(self, source, target):
        self.source = source
        self.target = target



class TranRequestHandler(SimpleHTTPRequestHandler, SimpleXMLRPCRequestHandler):
    language = None
    renderers = [gnome_renderer(), kde_renderer(), mozilla_renderer()]

    def send_error(self, code, message=None):
        try:
            short, explain = self.responses[code]
        except KeyError:
            short, explain = '???', '???'
        if message is None:
            message = short
        self.log_error("code %d, message %s", code, message)
        content = "<h1>%d %s</h1><p>%s</p>" % (code, short, explain)
        content = content.encode('utf-8')
        if self.command != 'HEAD' and code >= 200 and code not in (204, 304):
            f = self.embed_in_template(content, code)
            self.copyfile(f, self.wfile)


    def render_all(self):
        needplus = False
        result = ""
        for r in TranRequestHandler.renderers:
            icon = r.render_icon(needplus)
            if icon != "":
                needplus = True
            result += icon
        return result


    def render_div(self, idx):
        result = '<div id="sug%d">' % idx
        for r in TranRequestHandler.renderers:
            result += r.render_links(self.language)
        return result + "</div>\n"


    def render_suggestions(self, suggs):
        result = '<ol>\n'
        idx = 1
        for s in suggs:
            result += '<li value="%d"><a href="#" onclick="return blocking(\'sug%d\')">%s (' % (s.value, idx, _replace_html(s.text))
            for r in TranRequestHandler.renderers:
                r.clear()
            for p in s.projects:
                for r in TranRequestHandler.renderers:
                    r.feed(p)
            result += self.render_all()
            result += ')</a>'
            result += self.render_div(idx)
            result += '</li>\n'
            idx += 1
        result += '</ol>\n'
        return result

    def dump(self, responses):
        rtl = ''
        if self.language in RTL_LANGUAGES:
            rtl = ' dir="rtl" style="text-align: right"'
        body = u'<h1>%s</h1><dl%s>' % (SUGGESTIONS_TXT.get(self.language, u'Translation suggestions'), rtl)
        for key, suggs in responses:
            body += '<di><dt><strong>%s</strong></dt>\n<dd>%s</dd></di>' % (_replace_html(key), self.render_suggestions(suggs))
        body += "</dl>"
        return body


    def get_file(self):
        data = self.rfile.read(int(self.headers["content-length"]))
        msg = email.message_from_string(str(self.headers) + data)
        i = msg.walk()
        i.next()
        part = i.next()
        cls = factory.getclass(part.get_filename())
        return cls.parsestring(part.get_payload(decode=1))

    
    def suggest(self, text):
        phrase = Phrase(text, self.language, False)
        suggs = self.server.storage.suggest(phrase.canonical(), self.language)
        return (text, suggs)


    def suggest_unit(self, unit):
        return self.suggest(str(unit.source))


    def translate(self):
        storage = self.get_file()
        suggs = map(self.suggest_unit, storage.units)
        return self.dump(suggs).encode('utf-8')


    def shutdown(self, errcode):
        self.send_error(errcode)
        self.wfile.flush()
        self.connection.shutdown(1)
        return


    def get_language(self):
        try:
            prefix = self.headers['Host'].split('.')[0]
            prefix = prefix.replace('-', '_')
            if prefix in LANGUAGES:
                self.language = prefix
        except:
            pass
    
    
    def send_plain_headers(self, code, ctype, length):
        self.send_response(code)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(length))
        self.end_headers()


    def find_template(self):
        if self.language == None:
            path = self.translate_path('/template.html')
        else:
            path = self.translate_path('/' + self.language + '/template.html')
        return open(path, 'rb')


    def embed_in_template(self, text, code=200):
        template = self.find_template()
        f = StringIO()
        for line in template:
            if line.find('<content/>') != -1:
                if isinstance(text, file):
                    self.copyfile(text, f)
                else:
                    f.write(text)
            else:
                f.write(line)

        f.flush()
        length = f.tell()
        f.seek(0)
        self.send_plain_headers(code, "text/html", length)
        return f


    def send_search_head(self):
        query = None
        plen = len(self.path)
        if plen > 8 and self.path[8] == '/':
            query = urllib.unquote(self.path[9:])
        elif plen > 8 and self.path[8:11] == '?q=':
            query = urllib.unquote(self.path[11:])

        if query == None or self.language == None:
            return self.shutdown(404)

        query = query.replace('+', ' ')
        response = self.dump([self.suggest(query)]).encode('utf-8')
        return self.embed_in_template(response)
        

    def send_head(self):
        if self.path.startswith('/suggest'):
            return self.send_search_head()

        if self.language == None:
            path = self.translate_path(self.path)
        else:
            path = self.translate_path('/' + self.language + '/' + self.path)
        f = None
        if os.path.isdir(path):
            index = os.path.join(path, "index.html")
            if os.path.exists(index):
                path = index
            else:
                self.send_error(404, "File not found")
                return None

        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
            if path.endswith('.html'):
                return self.embed_in_template(f)
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_plain_headers(200, ctype, os.fstat(f.fileno())[6])
        return f


    def list_directory(self, path):
        self.send_error(404, "File not found")
        return None


    def do_POST(self):
        self.get_language()
        
        if self.path == '/RPC2':
            return SimpleXMLRPCRequestHandler.do_POST(self)
        try:
            response = self.translate()
        except:
            return self.shutdown(403)
        f = self.embed_in_template(response)
        self.copyfile(f, self.wfile)


    def do_GET(self):
        self.get_language()
        return SimpleHTTPRequestHandler.do_GET(self)

        


class TranServer(ThreadingMixIn, SimpleXMLRPCServer):
    allow_reuse_address = True

    def __init__(self, addr):
        signal(SIGPIPE, SIG_IGN)
        SimpleXMLRPCServer.__init__(self, addr, TranRequestHandler)
        self.storage = TranDB("C")
        self.register_function(lambda phrase, lang: self.storage.suggest(phrase, lang), 'suggest')
        self.register_introspection_functions()
        self.register_multicall_functions()
