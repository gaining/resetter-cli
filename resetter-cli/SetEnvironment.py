#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This class sets up distro specific settings and working directory

import errno
import lsb_release
import os
import pwd
import shutil
import sys
from termcolor import cprint


class Settings(object):

    def __init__(self):
        super(Settings, self).__init__()
        self.directory = ".resetter-cli/data"
        self.os_info = lsb_release.get_distro_information()
        self.euid = os.geteuid()
        self.detectRoot()
        self.manifests = '/usr/lib/resetter/data/manifests'
        self.userlists = '/usr/lib/resetter/data/userlists'
        if 'PKEXEC_UID' in os.environ:
            self.user = pwd.getpwuid(int(os.environ['PKEXEC_UID'])).pw_name
            working_dir = '/home/{}'.format(self.user)
            os.chdir(working_dir)
            print ('Welcome {}'.format(self.user))
        elif self.euid == 0 and 'PKEXEC_UID' not in os.environ:
            self.user = os.environ['SUDO_USER']
            print ('Welcome {}'.format(self.user))
        else:
            self.user = os.environ.get('USERNAME')
            print ('Welcome {}\n'.format(self.user))
        self.createDirs()
        if os.path.isdir(self.directory):
            os.chdir(self.directory)
        else:
            print ("ERROR: {} has not been created".format(self.directory))
        print(self.detectOS())
        self.manifest = ("{}/{}").format(self.manifests, self.detectOS()[0])
        self.userlist = ("{}/{}").format(self.userlists, self.detectOS()[1])
        self.window_title = self.detectOS()[2]
        self.filesExist(self.manifest, self.userlist)
        if os.path.exists(self.manifest):
            print ('Using: {}\n'.format(self.manifest))

    def detectRoot(self):  # root detection function
        if self.euid != 0:
            print ("Need to be root to run this program")
            exit(1)

    def createDirs(self):
        uid_change = pwd.getpwnam(self.user).pw_uid
        gid_change = pwd.getpwnam(self.user).pw_gid
        pidx = os.fork()
        if pidx == 0:
            try:
                os.setgid(gid_change)
                os.setuid(uid_change)
                if not os.path.exists(self.directory):
                    os.makedirs(self.directory)
                os.chdir(self.directory)
                man_dir = os.path.abspath('manifests')
                userlists_dir = os.path.abspath('userlists')
                self.copy(self.manifests, man_dir)
                self.copy(self.userlists, userlists_dir)
            except:
                Exception
            finally:
                os._exit(0)
        os.waitpid(pidx, 0)

    def copy(self, source, destination):
        try:
            shutil.copytree(source, destination)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                shutil.copy(source, destination)
            else:
               pass

    def detectOS(self):
        apt_locations = ('/usr/bin/apt', '/usr/lib/apt', '/etc/apt', '/usr/local/bin/apt')
        if any(os.path.exists(f) for f in apt_locations):
            manifest = self.os_info['ID'] + self.os_info['RELEASE'] + '.manifest'
            userlist = self.os_info['ID'] + self.os_info['RELEASE'] + '-default-userlist'
            window_title = self.os_info['ID']
            return manifest, userlist, window_title
        else:
            cprint("Apt could not be found, Your distro does not appear to be Debian based.",
                   'white', 'on_red', attrs=['bold', 'dark', 'reverse', 'underline'])
            sys.exit(1)

    def filesExist(self, manifest, userlist):
        if not os.path.isfile(manifest):
            print ("{} could not be found, please choose a manifest for your system if you have one".format(manifest))
        if not os.path.isfile(userlist):
                print ("userlist could not be found, features requiring this file will not work.")