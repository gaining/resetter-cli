#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This class sets up distro specific settings and working directory

import errno
import logging
import lsb_release
import os
import pwd
import shutil
import sys
from termcolor import colored, cprint

import sqlite3
import subprocess


class Test(object):

    def __init__(self):
        super(Test, self).__init__()
        self.os_info = lsb_release.get_lsb_information()
        print (self.os_info)
        print ("{} {}".format(self.os_info['ID'], self.os_info['RELEASE']))

Test()


