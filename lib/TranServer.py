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
from SocketServer import ForkingMixIn
from datetime import datetime
from signal import signal, alarm, SIGPIPE, SIGALRM, SIG_IGN
from suggest import TranDB
from translate.storage import factory
from tempfile import NamedTemporaryFile
from phrase import Phrase
from StringIO import StringIO
from urlparse import urlparse
from Cookie import SimpleCookie
from common import LANGUAGES

import email
import xmlrpclib
import urllib
import posixpath
import os
import stat
import sys
import logging


SUGGESTIONS_TXT = {
    'ar': u'﻿ترجمات مُقتَرَحة',
    'be_latin' : u'Prapanavanyja pierakłady',
    'ca' : u'Possibles traduccions',
    'csb': u'Sugerowóny dolmaczënczi',
    'da' : u'Oversćttelsesforslag',
    'de' : u'Übersetzungsvorschläge',
    'en' : u'Translation suggestions',
    'es' : u'Sugerencias de traducción',
    'fi' : u'Käännös ehdotukset',
    'fr' : u'Traductions suggérées',
    'fy' : u'Oersetsuggestjes',
    'gl' : u'Suxesti&oacute;ns de traduci&oacute;n',
    'he' : u'הצעות לתרגום',
    'it' : u'Suggerimenti traduzione',
    'ka' : u'თარგმნის შემოთავაზებები',
    'pl' : u'Sugestie tłumaczeń',
    'pt_br': u'Sugestões de tradução',
    'uk' : u'Запропоновані переклади'
    }


RTL_LANGUAGES = ['ar', 'fa', 'ha', 'he']


logging.basicConfig(level = logging.DEBUG,
                    format = '%(asctime)s %(levelname)-8s %(message)s',
                    datefmt = '%y-%m-%d|%H:%M',
                    filename = '/var/log/open-tran.log',
                    filemode = 'a')


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

    def feed(self, project):
        if project.path[0] == self.name[0]:
            self.projects.append(project)

    def render_icon(self):
        return '<img src="%s" alt="%s"/>' % (self.icon_path, self.name)

    def render_count(self, needplus):
        cnt = reduce(lambda x,y: x + y.count, self.projects, 0)
        if cnt == 0:
            return None
        if needplus:
            result = " + "
        else:
            result = ""
        if cnt > 1:
            result += "%d&times;" % cnt
        return result

    def render_icon_cnt(self, needplus):
        cnt = self.render_count(needplus)
        if cnt == None:
            return ""
        return  cnt + self.render_icon()
    
    def render_links(self, lang):
        result = ""
        for project in self.projects:
            if project.count > 1:
                result += "%d&times;" % project.count
            path = self.name + " " + project.path[2:]
            if project.flags == 1:
                result += '<span id="fuzzy">'
            result += "%s: %s<br/>\n" % (self.render_link(path), _replace_html(project.orig_phrase))
            if project.flags == 1:
                result += '</span>'
        return result

    def render_project_link(self):
        icon = self.render_icon()
        return self.render_link(icon + " " + self.name)


class gnome_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "GNOME"
        self.icon_path = "/images/gnome-logo.png"
    
    def render_link(self, project):
        return '<a href="http://www.gnome.org/i18n/">%s</a>' % project
    

class kde_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "KDE"
        self.icon_path = "/images/kde-logo.png"

    def render_link(self, project):
        return '<a href="http://l10n.kde.org/">%s</a>' % project


class mozilla_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "Mozilla"
        self.icon_path = "/images/mozilla-logo.png"

    def render_link(self, project):
        return '<a href="http://www.mozilla.org/projects/l10n/">%s</a>' % project


class fy_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "FY"
        self.icon_path = "/images/pompelyts.png"

    def render_link(self, project):
        return '<a href="http://members.chello.nl/~s.hiemstra/kompjtr.htm">%s</a>' % project.replace('FY', 'Cor Jousma')


class di_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "Debian Installer"
        self.icon_path = "/images/debian-logo.png"

    def render_link(self, project):
        return '<a href="http://d-i.alioth.debian.org/">%s</a>' % project


class suse_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "SUSE"
        self.icon_path = "/images/suse-logo.png"

    def render_link(self, project):
        return '<a href="http://i18n.opensuse.org/">%s</a>' % project


class xfce_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "XFCE"
        self.icon_path = "/images/xfce-logo.png"

    def render_link(self, project):
        return '<a href="http://i18n.xfce.org/">%s</a>' % project


class inkscape_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "Inkscape"
        self.icon_path = "/images/inkscape-logo.png"

    def render_link(self, project):
        return '<a href="http://www.inkscape.org">%s</a>' % project


class openoffice_renderer(renderer):
    def __init__(self):
        renderer.__init__(self)
        self.name = "OpenOffice.org"
        self.icon_path = "/images/oo-logo.png"

    def render_link(self, project):
        return '<a href="http://l10n.openoffice.org">%s</a>' % project



class Suggestion:
    def __init__(self, source, target):
        self.source = source
        self.target = target


RENDERERS = [
    di_renderer(),
    fy_renderer(),
    gnome_renderer(),
    inkscape_renderer(),
    kde_renderer(),
    mozilla_renderer(),
    openoffice_renderer(),
    suse_renderer(),
    xfce_renderer()
    ]



def rw_handler(signum, frame):
    raise IOError, 'Read/Write Timeout'


class FileWrapper:
    def __init__(self, socket):
        self.socket = socket
        signal(SIGALRM, rw_handler)
        for n in dir(self.socket):
            if not n[0:2] == '__' and n not in ['read', 'readline', 'write']:
                setattr(self, n, getattr(self.socket, n))

    def read(self, size = -1):
        alarm(45)
        result = self.socket.read(size)
        alarm(0)
        return result

    def readline(self, size = -1):
        alarm(45)
        result = self.socket.readline(size)
        alarm(0)
        return result

    def write(self, str):
        alarm(90)
        result = self.socket.write(str)
        alarm(0)
        return result



class TranRequestHandler(SimpleHTTPRequestHandler, DocXMLRPCRequestHandler):
    srclang = None
    dstlang = None
    ifacelang = None
    idx = 1

    def setup(self):
        self.connection = self.request
        self.rfile = FileWrapper(self.connection.makefile('rb', self.rbufsize))
        self.wfile = FileWrapper(self.connection.makefile('wb', self.wbufsize))


    def do_logging(self, level, format, *args):
	host = ""
	try:
	    host = self.headers['Host']
	except:
	    pass
	
	logging.log(level, '%s [%s] {%s} %s' % (host, self.ifacelang, self.address_string(), format % args))
        

    def log_error(self, *args):
        self.do_logging(logging.ERROR, *args)

    
    def log_message(self, format, *args):
	self.do_logging(logging.INFO, format, *args)


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
            icon = r.render_icon_cnt(needplus)
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
            result += '<li value="%d"><a href="javascript:;" class="jslink" onclick="return visibility_switch(\'sug%d\')">%s (' % (s.value, self.idx, _replace_html(s.text))
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


    def render_suggestions_compare(self, suggs, dstlang):
        cnt, sum = reduce(lambda x, y: (x[0] + 1, x[1] + len(y.text)), suggs, (0, 0))
        result = '<ol style="width: %dem">\n' % (sum / cnt * 2 / 3)
        for s in suggs:
            for r in RENDERERS:
                r.clear()
            for p in s.projects:
                for r in RENDERERS:
                    r.feed(p)
            for r in RENDERERS:
                cnt = r.render_count(False)
                if cnt != None:
                    break
            result += '<li value="%d">%s<a href="javascript:;" class="jslink" onclick="return visibility_switch(\'sug%d\')">%s</a>' % (s.value, cnt, self.idx, _replace_html(s.text))
            result += self.render_div(self.idx, dstlang)
            result += '</li>\n'
            self.idx += 1
        result += '</ol>\n'
        return result


    def render_project_link(self, project):
        for r in RENDERERS:
            r.clear()
            if r.name == project:
                return r.render_project_link()


    def dump(self, responses, srclang, dstlang):
        rtl = ''
        if dstlang in RTL_LANGUAGES:
            rtl = ' dir="rtl" style="text-align: right"'
        body = u'<h1>%s (%s &rarr; %s)</h1><dl%s>' % (SUGGESTIONS_TXT.get(self.ifacelang, u'Translation suggestions'), srclang, dstlang, rtl)
        for key, suggs in responses:
            body += u'<di><dt><strong>%s</strong></dt>\n<dd>%s</dd></di>' % (_replace_html(key), self.render_suggestions(suggs, dstlang))
        body += u"</dl>"
        return body


    def dump_compare(self, responses, lang):
        rtl = ''
        if lang in RTL_LANGUAGES:
            rtl = ' dir="rtl" style="text-align: right"'
        result = '<table%s>\n' % rtl
        head = ''
        body = ''
        for project, suggs in responses.iteritems():
            head += u'<th>%s</th>' % self.render_project_link(project)
            body += u'<td>%s</td>' % self.render_suggestions_compare(suggs, lang)
        result += '<tr>%s</tr>\n<tr>%s</tr>\n' % (head, body)
        result += '</table>'
        return result


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


    def get_src_dst_languages(self):
        langone = ""
        langtwo = ""
        try:
            langone = self.headers['Host'].split('.')[0].replace('-', '_')
            langtwo = self.headers['Host'].split('.')[1].replace('-', '_')
        except:
	    pass

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
            self.srclang = langone
            self.dstlang = 'en'

	
    def convert_iface_lang(self, lang):
        for l in SUGGESTIONS_TXT.keys():
            i = l.find('_')
	    if i < 0:
		i = len(l)
	    if lang[:i] == l[:i]:
                return l
        return None


    def get_iface_language(self):
	try:
            c = SimpleCookie(self.headers['Cookie'])
            self.ifacelang = self.convert_iface_lang(c['lang'].value)
            if self.ifacelang:
                return
        except:
            pass
        try:
            langs = self.headers['Accept-Language'].split(',')
            for lang in langs:
                self.ifacelang = self.convert_iface_lang(lang)
                if self.ifacelang:
                    return
        except:
            pass
        self.ifacelang = self.convert_iface_lang(self.srclang)
        if self.ifacelang:
            return
	self.ifacelang = self.convert_iface_lang(self.dstlang)
        if self.ifacelang:
            return
        self.ifacelang = "en"
	

    def get_languages(self):
        self.srclang = "en"
	self.dstlang = "en"
	self.ifacelang = "en"
	self.get_src_dst_languages()
	self.get_iface_language()
        if self.srclang == "en" and self.dstlang == "en":
            self.dstlang = self.ifacelang
    
    
    def set_language(self):
        referer = '/'
        try:
            referer = self.headers['Referer'].lower()
            idx = referer.find('open-tran.eu')
            if idx < 0:
                referer = '/'
            else:
                referer = referer[idx + len('open-tran.eu'):]
        except:
            pass
        query = urlparse(self.path)[4]
        idx = query.find('lang=')
        if idx < 0:
            lang = 'en'
        else:
            lang = query[idx + 5:]
        self.send_response(303)
        self.send_header('Location', referer)
        self.send_header('Set-Cookie', 'lang=%s; domain=.open-tran.eu' % lang)
        self.end_headers()


    def redirect(self, path):
        self.send_response(301)
        self.send_header('Location', path)
        self.end_headers()
        

    def send_plain_headers(self, code, ctype, length, inode):
        self.send_response(code)
        self.send_header("Content-type", ctype)
        if length != 0:
            self.send_header("Content-Length", str(length))
        if inode != 0:
            self.send_header("ETag", str(inode))
        self.end_headers()


    def find_template(self):
        if self.ifacelang != None and self.ifacelang in LANGUAGES:
            path = self.translate_path('/' + self.ifacelang + '/template.html')
        else:
            path = self.translate_path('/template.html')
        return open(path, 'rb')


    def write_flag(self, f, static = False):
        lang = self.ifacelang
        if lang not in SUGGESTIONS_TXT:
            lang = "en"
        prefix = ""
        if static:
            prefix = "sel-"
        f.write(("""
      <a href="javascript:;" class="jslink" onclick="return visibility_switch('lang_choice');">
        <img src="/images/%sflag-%s.png" alt="%s"/>&nbsp;%s</a>
""" % (prefix, lang, lang, LANGUAGES[lang])).encode('utf-8'))


    def write_iface_select(self, f):
	for lang in sorted(SUGGESTIONS_TXT.keys()):
	    f.write(('''
<li><a href="/setlang?lang=%s" class="jslink"><img src="/images/flag-%s.png" alt="%s"/>&nbsp;%s</a></li>
''' % (lang, lang, lang, LANGUAGES[lang])).encode('utf-8'))

    def write_language_select(self, f, chosen):
        for code in sorted(LANGUAGES.keys()):
            f.write('<option value="%s"' % code)
            if code == chosen:
                f.write(' selected="selected"')
            f.write('>%s: %s</option>' % (code, LANGUAGES[code].encode('utf-8')))
        

    def process(self, stream, code=200):
	f = StringIO()
	for line in stream:
	    if line.find('<ifacelang/>') != -1:
                self.write_flag(f)
	    elif line.find('<sifacelang/>') != -1:
                self.write_flag(f, True)
            elif line.find('<ifaceselect/>') != -1:
		self.write_iface_select(f)
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
        f.seek(0)
	return f


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
        f.seek(0)
	result = self.process(f, code)
        length = result.tell()
	f.close()
        self.send_plain_headers(code, "text/html", length, 0)
        return result


    def get_query(self):
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
            return None
        return query.replace('+', ' ').decode('utf-8')


    def send_search_head(self):
        query = self.get_query()
        if query == None:
            self.shutdown(404)
        response = self.dump([self.suggest(query, self.srclang, self.dstlang)], self.srclang, self.dstlang).encode('utf-8')
        response += self.dump([self.suggest(query, self.dstlang, self.srclang)], self.dstlang, self.srclang).encode('utf-8')
        return self.embed_in_template(response)


    def send_compare_head(self):
        query = self.get_query()
        if query == None:
            self.shutdown(404)
        lang = self.srclang
        if lang == "en":
            lang = self.dstlang
        suggs = self.server.storage.compare(query, lang)
        response = self.dump_compare(suggs, lang).encode('utf-8')
        return self.embed_in_template(response)
        

    def send_head(self):
        if self.path.startswith('/setlang'):
            return self.set_language()

        if self.path.startswith('/suggest'):
            return self.send_search_head()

        if self.path.startswith('/compare'):
            return self.send_compare_head()

        path = self.translate_path('/' + self.ifacelang + '/' + self.path)
        f = None
        if os.path.isdir(path):
            index = os.path.join(path, "index.shtml")
            if os.path.exists(index):
                path = index
            else:
                self.send_error(404, "File not found")
                return None

        ctype = self.guess_type(path)

        if path.endswith('index.html'):
            self.redirect('/index.shtml')
            return None
        
        try:
            f = open(path, 'rb')
            if path.endswith('.html'):
                return self.embed_in_template(f)
	    elif path.endswith('.shtml'):
		return self.process(f)
        except IOError:
            self.send_error(404, "File not found")
            return None
        fs = os.fstat(f.fileno())
        if 'if-none-match' in self.headers and self.headers['if-none-match'] == str(fs[stat.ST_INO]):
            self.send_plain_headers(304, ctype, 0, 0)
            return None
        else:
            self.send_plain_headers(200, ctype, fs[stat.ST_SIZE], fs[stat.ST_INO])
        return f


    def list_directory(self, path):
        self.send_error(404, "File not found")
        return None


    def do_POST(self):
        self.get_languages()
        if self.path == '/RPC2':
            return DocXMLRPCRequestHandler.do_POST(self)
        else:
            return self.shutdown(403)


    def do_GET(self):
        self.get_languages()
        if self.path == '/RPC2':
            return DocXMLRPCRequestHandler.do_GET(self)
        return SimpleHTTPRequestHandler.do_GET(self)

        


class TranServer(ForkingMixIn, DocXMLRPCServer):
    max_children = 70
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
        self.storage = TranDB('../data/')
        self.register_function(self.storage.suggest3, 'suggest3')
        self.register_function(self.storage.suggest2, 'suggest2')
        self.register_function(self.storage.suggest, 'suggest')
        self.register_function(self.storage.compare, 'compare')
        self.register_function(self.supported, 'supported')
        self.register_introspection_functions()
