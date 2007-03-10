#!/usr/bin/env python2.4
# -*- coding: utf-8 -*-

import ConfigParser, os

class Value(object):
    def __init__(self, config, key):
        self.__config = config
        self.__key = key

    def get(self, conf):
        return self.__config.get(conf.SECTION, self.__key)

    def set(self, conf, value):
        self.__config.set(conf.SECTION, self.__key, value)


class Hook:
    def __init__(self, fun, option):
        self.__fun = fun
        self.__option = option;

    def run(self, config):
        setattr(config, self.__option, self.__fun())


class Settings(object):
    SECTION = "user"
    
    def __init__(self):
        self.__hooks = []
        self.__config = ConfigParser.ConfigParser({"width": "640",
                                                   "height": "480",
                                                   "src_heigth" : "150",
                                                   "dst_heigth" : "150",
                                                   "correct_width" : "320",
                                                   "file" : "",
                                                   "folder" : "",
                                                   "phrase_index" : "1"})
        self.__config.read(os.path.expanduser('~/.tran/config'))
        if not self.__config.has_section(Settings.SECTION):
            self.__config.add_section(Settings.SECTION)
        for key in self.__config.options(Settings.SECTION):
            val = Value(self.__config, key)
            setattr(Settings, key, property(val.get, val.set))


    def onquit(self):
        for hook in self.__hooks:
            hook.run(self)
        f = open(os.path.expanduser('~/.tran/config'), 'w')
        self.__config.write(f)
        f.close()

    def register(self, fun, option):
        self.__hooks.append(Hook(fun, option))
