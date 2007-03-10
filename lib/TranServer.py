#!/usr/bin/env python2.4
# -*- coding: utf-8 -*-

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


LANGUAGES = {
    'de' : u'Übersetzungsvorschläge',
    'es' : u'Sugerencias de traducción',
    'fr' : u'Translation suggestions',
    'it' : u'Translation suggestions',
    'ja' : u'Translation suggestions',
    'nl' : u'Translation suggestions',
    'pl' : u'Sugestie tłumaczeń',
    'pt' : u'Translation suggestions',
    'pt_br' : u'Translation suggestions',
    'ru' : u'Translation suggestions',
    'sv' : u'Translation suggestions',
    'tr' : u'Translation suggestions'
    }


def _replace_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')



class Suggestion:
    def __init__(self, source, target):
        self.source = source
        self.target = target



class TranRequestHandler(SimpleHTTPRequestHandler, SimpleXMLRPCRequestHandler):
    language = None

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


    def dump(self, responses):
        body = u'<h1>%s</h1><table border="1">' % LANGUAGES[self.language]
        for key, suggs in responses:
            if len(suggs) == 0:
                continue
            body += '<tr><td valign="top" rowspan="%d">%s</td><td>' % (len(suggs), _replace_html(key))
            for s in suggs[:-1]:
                body += "%s</td></tr>\n<tr><td>" % _replace_html(s)
            body += "%s</td></tr>\n" % _replace_html(suggs[len(suggs)-1])
        body += "</table>"
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
