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

from DocXMLRPCServer import DocXMLRPCRequestHandler, DocXMLRPCServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from SocketServer import ThreadingMixIn
from signal import signal, SIGPIPE, SIG_IGN
from suggest import TranDB
from translate.storage import factory
from tempfile import NamedTemporaryFile
from phrase import Phrase
from StringIO import StringIO
from urlparse import urlparse
from Cookie import SmartCookie

import email
import xmlrpclib
import urllib
import posixpath
import os


SUGGESTIONS_TXT = {
    'ar': u'﻿ترجمات مُقتَرَحة',
    'be_latin' : u'Prapanavanyja pierakłady',
    'ca' : u'Possibles traduccions',
    'csb': u'Sugerowóny dolmaczënczi',
    'da' : u'Oversćttelsesforslag',
    'de' : u'Übersetzungsvorschläge',
    'es' : u'Sugerencias de traducción',
    'fi' : u'Käännös ehdotukset',
    'fr' : u'Traductions suggérées',
    'fy' : u'Oersetsuggestjes',
    'gl' : u'Suxesti&oacute;ns de traduci&oacute;n',
    'it' : u'Suggerimenti traduzione',
    'pl' : u'Sugestie tłumaczeń',
    'uk' : u'Запропоновані переклади'
    }

LANGUAGES = {
    'af' : u'Afrikaans',
    'ar' : u'العربية',
    'az' : u'Azərbaycan',
    'be' : u'Беларуская',
    'be_latin' : u'Biełaruskaja',
    'bg' : u'Български',
    'bn' : u'বাংলা',
    'br' : u'Brezhoneg',
    'bs' : u'Bosanski',
    'ca' : u'Català',
    'cs' : u'Čeština',
    'csb' : u'Kaszëbsczi',
    'cy' : u'Cymraeg',
    'da' : u'Dansk',
    'de' : u'Deutsch',
    'el' : u'Ελληνικά',
    'en' : u'English',
    'en_gb' : u'English',
    'eo' : u'Esperanto',
    'es' : u'Español',
    'et' : u'Eesti',
    'eu' : u'Euskara',
    'fa' : u'فارسی',
    'fi' : u'Suomi',
    'fo' : u'Føroyskt',
    'fr' : u'Français',
    'fy' : u'Frysk',
    'ga' : u'Gaeilge',
    'gl' : u'Galego',
    'ha' : u'هَوُسَ',
    'he' : u'‫עברית‬',
    'hi' : u'हिन्दी',
    'hr' : u'Hrvatski',
    'hsb' : u'Hornjoserbsce',
    'hu' : u'Magyar',
    'id' : u'Bahasa Indonesia',
    'is' : u'Íslenska',
    'it' : u'Italiano',
    'ja' : u'日本語',
    'ka' : u'ქართული',
    'kk' : u'Қазақша',
    'km' : u'ភាសាខ្មែរ',
    'ko' : u'한국어',
    'ku' : u'Kurdî/كوردی',
    'lb' : u'Lëtzebuergesch',
    'lo' : u'ລາວ',
    'lt' : u'Lietuvių',
    'lv' : u'Latviešu',
    'mg' : u'Malagasy',
    'mi' : u'Māori',
    'mk' : u'Македонски',
    'mn' : u'Монгол',
    'ms' : u'Bahasa Melayu',
    'mt' : u'bil-Malti',
    'nb' : u'Norsk bokmål',
    'nds' : u'Plattdüütsch',
    'ne' : u'नेपाली',
    'nl' : u'Nederlands',
    'nn' : u'Norsk nynorsk',
    'oc' : u'Occitan',
    'pa' : u'ਪਜਾਬੀ/पंजाबी/پنجابي',
    'pl' : u'Polski',
    'pt' : u'Português',
    'pt_br' : u'Português',
    'ro' : u'Română',
    'ru' : u'Руccкий',
    'rw' : u'Ikinyarwanda',
    'se' : u'Sámegiella',
    'sk' : u'Slovenčina',
    'sl' : u'Slovenščina',
    'sq' : u'Shqip',
    'sr' : u'Српски',
    'sr_latn' : u'Srpski',
    'ss' : u'SiSwati',
    'sv' : u'Svenska',
    'ta' : u'தமிழ்',
    'te' : u'తెలుగు',
    'tg' : u'Тоҷикӣ',
    'th' : u'ไทย',
    'tr' : u'Türkçe',
    'tt' : u'Tatarça/Татарча',
    'uk' : u'Українська',
    'uz' : u'Ўзбек',
    'ven' : u'Tshivenda',
    'vi' : u'Tiếng Việt',
    'wa' : u'Walon',
    'xh' : u'isiXhosa',
    'zh_cn' : u'古文/文言文',
    'zh_hk' : u'古文/文言文',
    'zh_tw' : u'古文/文言文',
    'zu' : u'isiZulu'
    }

RTL_LANGUAGES = ['ar', 'fa', 'ha', 'he']


def _replace_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')



class renderer(object):
    def __init__(self):
        self.projects = []
        self.langs = { 'be_latin' : 'be@latin',
                       'en_gb' : 'en_GB',
                       'pt_br' : 'pt_BR',
                       'sr_latn' : 'sr@Latn',
                       'zh_cn' : 'zh_CN',
                       'zh_hk' : 'zh_HK',
                       'zh_tw' : 'zh_TW' }
    
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
        self.icon_path = "/images/gnome-logo.png"
    
    def may_render(self, project):
        return project.path[0] == 'G'

    def render_link(self, path, lang):
        path = path[2:]
        fname = os.path.basename(path)
        while len(path):
            path, rest = os.path.split(path)
        if lang in self.langs:
            lang = self.langs[lang]
        return '<a href="http://svn.gnome.org/viewvc/%s/trunk/po/%s.po">GNOME %s</a>' % (rest, lang, rest)
    

class kde_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "KDE"
        self.icon_path = "/images/kde-logo.png"

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
        self.icon_path = "/images/mozilla-logo.png"

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

class fy_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "FY"
        self.icon_path = "/images/pompelyts.png"

    def may_render(self, project):
        return project.path[0] == 'F'

    def render_link(self, path, lang):
        return '<a href="http://members.chello.nl/~s.hiemstra/kompjtr.htm">Cor Jousma</a>'


class di_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "DI"
        self.icon_path = "/images/debian-logo.png"

    def may_render(self, project):
        return project.path[0] == 'D'
    
    def render_link(self, path, lang):
        if lang in self.langs:
            lang = self.langs[lang]
        return '<a href="http://d-i.alioth.debian.org/l10n-stats/level1/master/%s.po">Debian Installer</a>' % lang


class Suggestion:
    def __init__(self, source, target):
        self.source = source
        self.target = target


RENDERERS = [gnome_renderer(), kde_renderer(), mozilla_renderer(), fy_renderer(), di_renderer()]


class TranRequestHandler(SimpleHTTPRequestHandler, DocXMLRPCRequestHandler):
    srclang = None
    dstlang = None
    ifacelang = None
    idx = 1

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
        for r in RENDERERS:
            icon = r.render_icon(needplus)
            if icon != "":
                needplus = True
            result += icon
        return result


    def render_div(self, idx, dstlang):
        result = '<div id="sug%d" dir="ltr">' % idx
        for r in RENDERERS:
            result += r.render_links(dstlang)
        return result + "</div>\n"


    def render_suggestions(self, suggs, dstlang):
        result = '<ol>\n'
        for s in suggs:
            result += '<li value="%d"><a href="#" class="jslink" onclick="return blocking(\'sug%d\')">%s (' % (s.value, self.idx, _replace_html(s.text))
            for r in RENDERERS:
                r.clear()
            for p in s.projects:
                for r in RENDERERS:
                    r.feed(p)
            result += self.render_all()
            result += ')</a>'
            result += self.render_div(self.idx, dstlang)
            result += '</li>\n'
            self.idx += 1
        result += '</ol>\n'
        return result

    def dump(self, responses, srclang, dstlang):
        rtl = ''
        if dstlang in RTL_LANGUAGES:
            rtl = ' dir="rtl" style="text-align: right"'
        body = u'<h1>%s (%s &rarr; %s)</h1><dl%s>' % (SUGGESTIONS_TXT.get(self.ifacelang, u'Translation suggestions'), srclang, dstlang, rtl)
        for key, suggs in responses:
            body += u'<di><dt><strong>%s</strong></dt>\n<dd>%s</dd></di>' % (_replace_html(key), self.render_suggestions(suggs, dstlang))
        body += u"</dl>"
        return body


    def get_file(self):
        data = self.rfile.read(int(self.headers["content-length"]))
        msg = email.message_from_string(str(self.headers) + data)
        i = msg.walk()
        i.next()
        part = i.next()
        cls = factory.getclass(part.get_filename())
        return cls.parsestring(part.get_payload(decode=1))

    
    def suggest(self, text, srclang, dstlang):
        suggs = self.server.storage.suggest2(text, srclang, dstlang)
        return (text, suggs)


    def suggest_unit(self, unit):
        return self.suggest(str(unit.source), self.srclang, self.dstlang)


    def shutdown(self, errcode):
        self.send_error(errcode)
        self.wfile.flush()
        self.connection.shutdown(1)
        return


    def get_language(self):
        self.ifacelang = "en"
        try:
            langone = self.headers['Host'].split('.')[0].replace('-', '_')
            langtwo = self.headers['Host'].split('.')[1].replace('-', '_')
        except:
            try:
                query = urlparse(self.path)[4]
                vars = [x.strip().split('=') for x in query.split('&')]
                langone = filter(lambda x: x[0] == 'src', vars)[0][1]
                langtwo = filter(lambda x: x[0] == 'dst', vars)[0][1]
            except:
                pass
        if langone in LANGUAGES and langtwo in LANGUAGES:
            self.srclang = langone
            self.dstlang = langtwo
        elif langone in LANGUAGES:
            self.srclang = 'en'
            self.dstlang = langone
            self.ifacelang = langone
        try:
            langs = map(lambda x: x[:2], self.headers['Accept-Language'].split(','))
            for lang in langs + [self.dstlang, self.srclang]:
                if lang in LANGUAGES:
                    self.ifacelang = lang
                    break
            c = SmartCookie(self.headers['Cookie'])
            self.ifacelang = c['lang'].value
        except:
            pass
    
    
    def set_language(self):
        query = urlparse(self.path)[4]
        idx = query.find('lang=')
        if idx < 0:
            lang = 'en'
        else:
            lang = query[idx + 5:]
        self.send_response(302)
        self.send_header('Location', '/')
        self.send_header('Set-Cookie', 'lang=%s; domain=.open-tran.eu' % lang)
        self.end_headers()

    def send_plain_headers(self, code, ctype, length):
        self.send_response(code)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(length))
        self.end_headers()


    def find_template(self):
        if self.ifacelang != None and self.ifacelang in LANGUAGES:
            path = self.translate_path('/' + self.ifacelang + '/template.html')
        else:
            path = self.translate_path('/template.html')
        return open(path, 'rb')


    def write_flag(self, f):
        lang = self.ifacelang
        if lang not in SUGGESTIONS_TXT:
            lang = "en"
        f.write("""
      <a href="javascript:;" class="jslink" onclick="return blocking('lang_choice');">Locale: <img src="/images/flag-%s.png" alt="%s"/></a>
""" % (lang, lang))


    def write_language_select(self, f, chosen):
        for code in sorted(LANGUAGES.keys()):
            f.write('<option value="%s"' % code)
            if code == chosen:
                f.write(' selected="selected"')
            f.write('>%s: %s</option>' % (code, LANGUAGES[code].encode('utf-8')))
        

    def embed_in_template(self, text, code=200):
        template = self.find_template()
        f = StringIO()
        for line in template:
            if line.find('<content/>') != -1:
                if isinstance(text, file):
                    self.copyfile(text, f)
                else:
                    f.write(text)
            elif line.find('<ifacelang/>') != -1:
                self.write_flag(f)
            elif line.find('<srclang/>') != -1:
                lang = self.srclang
                if lang == None:
                    lang = self.ifacelang
                self.write_language_select(f, lang)
            elif line.find('<dstlang/>') != -1:
                lang = self.dstlang
                if lang == None:
                    lang = "en"
                self.write_language_select(f, lang)
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
        elif plen > 8 and self.path[8] == '?':
            try:
                urlquery = urlparse(self.path)[4]
                vars = [x.strip().split('=') for x in urlquery.split('&')]
                query = filter(lambda x: x[0] == 'q', vars)[0][1]
                query = urllib.unquote(query)
            except:
                pass

        if query == None or self.dstlang == None:
            return self.shutdown(404)

        query = query.replace('+', ' ').decode('utf-8')
        response = self.dump([self.suggest(query, self.srclang, self.dstlang)], self.srclang, self.dstlang).encode('utf-8')
        response += self.dump([self.suggest(query, self.dstlang, self.srclang)], self.dstlang, self.srclang).encode('utf-8')
        return self.embed_in_template(response)
        

    def send_head(self):
        if self.path.startswith('/setlang'):
            return self.set_language()

        if self.path.startswith('/suggest'):
            return self.send_search_head()

        path = self.translate_path('/' + self.ifacelang + '/' + self.path)
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
            return DocXMLRPCRequestHandler.do_POST(self)
        else:
            return self.shutdown(403)


    def do_GET(self):
        self.get_language()
        if self.path == '/RPC2':
            return DocXMLRPCRequestHandler.do_GET(self)
        return SimpleHTTPRequestHandler.do_GET(self)

        


class TranServer(ThreadingMixIn, DocXMLRPCServer):
    allow_reuse_address = True

    def supported(self, lang):
        """
Checks if the service is capable of suggesting translations from or to
'lang' and returns True if it is.
"""
        return lang in LANGUAGES

    def __init__(self, addr):
        signal(SIGPIPE, SIG_IGN)
        DocXMLRPCServer.__init__(self, addr, TranRequestHandler)
        self.set_server_title('Open-Tran.eu')
        self.set_server_name('Open-Tran.eu XML-RPC API documentation')
        self.set_server_documentation('''
This server exports the following methods through the XML-RPC protocol.
''')
        self.storage = TranDB()
        self.register_function(self.storage.suggest2, 'suggest2')
        self.register_function(self.storage.suggest, 'suggest')
        self.register_function(self.supported, 'supported')
        self.register_introspection_functions()
