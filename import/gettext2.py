#!/usr/bin/env python2.4

import locale, copy, os, re, struct, sys


def test(condition, true, false):
    """
    Implements the C expression:

      condition ? true : false

    Required to correctly interpret plural forms.
    """
    if condition:
        return true
    else:
        return false


def c2py(plural):
    """Gets a C expression as used in PO files for plural forms and returns a
    Python lambda function that implements an equivalent expression.
    """
    # Security check, allow only the "n" identifier
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    import token, tokenize
    tokens = tokenize.generate_tokens(StringIO(plural).readline)
    try:
        danger = [x for x in tokens if x[0] == token.NAME and x[1] != 'n']
    except tokenize.TokenError:
        raise ValueError, \
              'plural forms expression error, maybe unbalanced parenthesis'
    else:
        if danger:
            raise ValueError, 'plural forms expression could be dangerous'

    # Replace some C operators by their Python equivalents
    plural = plural.replace('&&', ' and ')
    plural = plural.replace('||', ' or ')

    expr = re.compile(r'\!([^=])')
    plural = expr.sub(' not \\1', plural)

    # Regular expression and replacement function used to transform
    # "a?b:c" to "test(a,b,c)".
    expr = re.compile(r'(.*?)\?(.*?):(.*)')
    def repl(x):
        return "test(%s, %s, %s)" % (x.group(1), x.group(2),
                                     expr.sub(repl, x.group(3)))

    # Code to transform the plural expression, taking care of parentheses
    stack = ['']
    for c in plural:
        if c == '(':
            stack.append('')
        elif c == ')':
            if len(stack) == 1:
                # Actually, we never reach this code, because unbalanced
                # parentheses get caught in the security check at the
                # beginning.
                raise ValueError, 'unbalanced parenthesis in plural form'
            s = expr.sub(repl, stack.pop())
            stack[-1] += '(%s)' % s
        else:
            stack[-1] += c
    plural = expr.sub(repl, stack.pop())

    return eval('lambda n: int(%s)' % plural)



def _expand_lang(locale):
    from locale import normalize
    locale = normalize(locale)
    COMPONENT_CODESET   = 1 << 0
    COMPONENT_TERRITORY = 1 << 1
    COMPONENT_MODIFIER  = 1 << 2
    # split up the locale into its base components
    mask = 0
    pos = locale.find('@')
    if pos >= 0:
        modifier = locale[pos:]
        locale = locale[:pos]
        mask |= COMPONENT_MODIFIER
    else:
        modifier = ''
    pos = locale.find('.')
    if pos >= 0:
        codeset = locale[pos:]
        locale = locale[:pos]
        mask |= COMPONENT_CODESET
    else:
        codeset = ''
    pos = locale.find('_')
    if pos >= 0:
        territory = locale[pos:]
        locale = locale[:pos]
        mask |= COMPONENT_TERRITORY
    else:
        territory = ''
    language = locale
    ret = []
    for i in range(mask+1):
        if not (i & ~mask):  # if all components for this combo exist ...
            val = language
            if i & COMPONENT_TERRITORY: val += territory
            if i & COMPONENT_CODESET:   val += codeset
            if i & COMPONENT_MODIFIER:  val += modifier
            ret.append(val)
    ret.reverse()
    return ret


class NullTranslations:
    def __init__(self, fp=None):
        self._info = {}
        self._charset = None
        self._output_charset = None
        self._fallback = None
        if fp is not None:
            self._parse(fp)

    def _parse(self, fp):
        pass

    def add_fallback(self, fallback):
        if self._fallback:
            self._fallback.add_fallback(fallback)
        else:
            self._fallback = fallback

    def gettext(self, message):
        if self._fallback:
            return self._fallback.gettext(message)
        return message

    def lgettext(self, message):
        if self._fallback:
            return self._fallback.lgettext(message)
        return message

    def ngettext(self, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.ngettext(msgid1, msgid2, n)
        if n == 1:
            return msgid1
        else:
            return msgid2

    def lngettext(self, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.lngettext(msgid1, msgid2, n)
        if n == 1:
            return msgid1
        else:
            return msgid2

    def ugettext(self, message):
        if self._fallback:
            return self._fallback.ugettext(message)
        return unicode(message)

    def ungettext(self, msgid1, msgid2, n):
        if self._fallback:
            return self._fallback.ungettext(msgid1, msgid2, n)
        if n == 1:
            return unicode(msgid1)
        else:
            return unicode(msgid2)

    def info(self):
        return self._info

    def charset(self):
        return self._charset

    def output_charset(self):
        return self._output_charset

    def set_output_charset(self, charset):
        self._output_charset = charset

    def install(self, unicode=False, names=None):
        import __builtin__
        __builtin__.__dict__['_'] = unicode and self.ugettext or self.gettext
        if hasattr(names, "__contains__"):
            if "gettext" in names:
                __builtin__.__dict__['gettext'] = __builtin__.__dict__['_']
            if "ngettext" in names:
                __builtin__.__dict__['ngettext'] = (unicode and self.ungettext
                                                             or self.ngettext)
            if "lgettext" in names:
                __builtin__.__dict__['lgettext'] = self.lgettext
            if "lngettext" in names:
                __builtin__.__dict__['lngettext'] = self.lngettext


class GNUTranslations(NullTranslations):
    # Magic number of .mo files
    LE_MAGIC = 0x950412deL
    BE_MAGIC = 0xde120495L

    def _parse(self, fp):
        """Override this method to support alternative .mo formats."""
        unpack = struct.unpack
        filename = getattr(fp, 'name', '')
        # Parse the .mo file header, which consists of 5 little endian 32
        # bit words.
        self._catalog = self.catalog = catalog = {}
        self.plural = lambda n: int(n != 1) # germanic plural by default
        buf = fp.read()
        buflen = len(buf)
        # Are we big endian or little endian?
        magic = unpack('<I', buf[:4])[0]
        if magic == self.LE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('<4I', buf[4:20])
            ii = '<II'
        elif magic == self.BE_MAGIC:
            version, msgcount, masteridx, transidx = unpack('>4I', buf[4:20])
            ii = '>II'
        else:
            raise IOError(0, 'Bad magic number', filename)
        # Now put all messages from the .mo file buffer into the catalog
        # dictionary.
        for i in xrange(0, msgcount):
            mlen, moff = unpack(ii, buf[masteridx:masteridx+8])
            mend = moff + mlen
            tlen, toff = unpack(ii, buf[transidx:transidx+8])
            tend = toff + tlen
            if mend < buflen and tend < buflen:
                msg = buf[moff:mend]
                tmsg = buf[toff:tend]
            else:
                raise IOError(0, 'File is corrupt', filename)
            # See if we're looking at GNU .mo conventions for metadata
            if mlen == 0:
                # Catalog description
                lastk = k = None
                for item in tmsg.splitlines():
                    item = item.strip()
                    if not item:
                        continue
                    if ':' in item:
                        k, v = item.split(':', 1)
                        k = k.strip().lower()
                        v = v.strip()
                        self._info[k] = v
                        lastk = k
                    elif lastk:
                        self._info[lastk] += '\n' + item
                    if k == 'content-type':
                        self._charset = v.split('charset=')[1]
                    elif k == 'plural-forms':
                        v = v.split(';')
                        plural = v[1].split('plural=')[1]
                        self.plural = c2py(plural)
            # Note: we unconditionally convert both msgids and msgstrs to
            # Unicode using the character encoding specified in the charset
            # parameter of the Content-Type header.  The gettext documentation
            # strongly encourages msgids to be us-ascii, but some appliations
            # require alternative encodings (e.g. Zope's ZCML and ZPT).  For
            # traditional gettext applications, the msgid conversion will
            # cause no problems since us-ascii should always be a subset of
            # the charset encoding.  We may want to fall back to 8-bit msgids
            # if the Unicode conversion fails.
            if '\x00' in msg:
                # Plural forms
                msgid1, msgid2 = msg.split('\x00')
                tmsg = tmsg.split('\x00')
                if self._charset:
                    msgid1 = unicode(msgid1, self._charset)
                    tmsg = [unicode(x, self._charset) for x in tmsg]
                for i in range(len(tmsg)):
                    catalog[(msgid1, i)] = tmsg[i]
            else:
                if self._charset:
                    msg = unicode(msg, self._charset)
                    tmsg = unicode(tmsg, self._charset)
                catalog[msg] = tmsg
            # advance to next entry in the seek tables
            masteridx += 8
            transidx += 8

    def gettext(self, message):
        missing = object()
        tmsg = self._catalog.get(message, missing)
        if tmsg is missing:
            if self._fallback:
                return self._fallback.gettext(message)
            return message
        # Encode the Unicode tmsg back to an 8-bit string, if possible
        if self._output_charset:
            return tmsg.encode(self._output_charset)
        elif self._charset:
            return tmsg.encode(self._charset)
        return tmsg

    def lgettext(self, message):
        missing = object()
        tmsg = self._catalog.get(message, missing)
        if tmsg is missing:
            if self._fallback:
                return self._fallback.lgettext(message)
            return message
        if self._output_charset:
            return tmsg.encode(self._output_charset)
        return tmsg.encode(locale.getpreferredencoding())

    def ngettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog[(msgid1, self.plural(n))]
            if self._output_charset:
                return tmsg.encode(self._output_charset)
            elif self._charset:
                return tmsg.encode(self._charset)
            return tmsg
        except KeyError:
            if self._fallback:
                return self._fallback.ngettext(msgid1, msgid2, n)
            if n == 1:
                return msgid1
            else:
                return msgid2

    def lngettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog[(msgid1, self.plural(n))]
            if self._output_charset:
                return tmsg.encode(self._output_charset)
            return tmsg.encode(locale.getpreferredencoding())
        except KeyError:
            if self._fallback:
                return self._fallback.lngettext(msgid1, msgid2, n)
            if n == 1:
                return msgid1
            else:
                return msgid2

    def ugettext(self, message):
        missing = object()
        tmsg = self._catalog.get(message, missing)
        if tmsg is missing:
            if self._fallback:
                return self._fallback.ugettext(message)
            return unicode(message)
        return tmsg

    def ungettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog[(msgid1, self.plural(n))]
        except KeyError:
            if self._fallback:
                return self._fallback.ungettext(msgid1, msgid2, n)
            if n == 1:
                tmsg = unicode(msgid1)
            else:
                tmsg = unicode(msgid2)
        return tmsg



# trans = GNUTranslations(open('/home/sliwers/dl/soft/gajim-0.9/po/pl/LC_MESSAGES/gajim.mo', 'rb'))
# for k, v in trans.catalog.iteritems():
#     print repr(v)

