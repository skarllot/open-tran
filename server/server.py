#!/usr/bin/env python2.4
# -*- coding: utf-8 -*-

import sys
import signal
from TranServer import TranServer

print "loading...",
sys.stdout.flush()

server = TranServer(("localhost", 8080))

print "done."
sys.stdout.flush()

server.serve_forever()
