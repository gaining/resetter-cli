#!/usr/bin/python
import lsb_release
from SetEnvironment import Settings
from termcolor import colored, cprint
from picker import Picker
from Spinner import Spinner
import os
import sys
import subprocess
import datetime
import apt
import time

class ResetterMenu(object):
    def __init__(self, parent=None):
        cprint("RESETTER-CLI [ALPHA]", 'white', 'on_blue', attrs=['bold', 'underline'])

        self.loop = True
        self.euid = os.geteuid()
        self.os_info = lsb_release.get_lsb_information()
        self.d_env = Settings()
        self.spinner = Spinner()
        self.manifest = self.d_env.manifest
        self.userlist = self.d_env.userlist
        self.user = self.d_env.user
        self.isWritten = False
        self.isDone = False
        self.non_defaults = []

        # self.detectRoot()

    def menu(self):
        while self.loop:  # While loop which will keep going until loop = False
            cprint("1. Automatic Reset", 'white', 'on_blue',  attrs=['bold'])
            cprint("2. Custom Reset", 'white', 'on_blue',  attrs=['bold'])
            cprint("3. Fix broken packages", 'white', 'on_blue',  attrs=['bold'])
            cprint("4. Remove old kernels", 'white', 'on_blue',  attrs=['bold'])
            cprint("5. About",'white', 'on_blue', attrs=['bold'])
            cprint("6. Exit ", 'white', 'on_blue', attrs=['bold'])
            try:
                choice = int(input(colored("Choose an option [1-6]: ", 'blue',
                                               attrs=['bold'])))
                if choice == 1:
                    self.autoReset()

                elif choice == 2:
                    self.customReset()

                elif choice == 3:
                    self.fixBroken()

                elif choice == 4:
                    self.removeOldKernels()
                elif choice == 5:
                    print ("\n\nAlpha dev branch\n\n")

                elif choice == 6:
                    print("Goodbye")
                    self.loop = False
                else:
                    print("")
                    cprint("Invalid Choice", 'white', 'on_red', attrs=['bold'])
                    print("")


            except ValueError:
                print("")
                cprint("Invalid Choice", 'white', 'on_red', attrs=['bold'])
                print("")
    def autoReset(self):
        yes = set(['yes', 'y', ''])
        no = set(['no', 'n'])
        choice = input(colored("This will reset your " + str(self.os_info['DESCRIPTION']) +
                                   " installation to its factory defaults. "
                                   "Local user accounts and all their contents will also be removed. "
                                   "Are you sure you'd like to continue?: ",
                               'yellow')).lower()
        if str(choice).lower() in yes:
            rapps = []
            self.spinner.start()
            self.getMissingPackages()
            if self.lineCount('apps-to-remove') > 0:
                self.getLocalUserList()
                self.findNonDefaultUsers()
                with open('apps-to-remove') as atr:
                    for line in atr:
                        rapps.append(line)
                self.spinner.stop()
                rapps.sort()
                opts = Picker(
                    title='Automatic Reset: All of these packages will be removed',
                    options=rapps,
                    checkall=True,
                    mut=True
                ).getSelected()
                if not opts:
                    print('')
            else:
                print("All removable packages have already been removed, there are no more packages left")
        elif choice.lower() in no:
            pass
        else:
            print("Please respond with 'yes' or 'no'")

    def fixBroken(self):
        proc = subprocess.Popen(['bash', '/usr/lib/resetter/data/scripts/fix-broken.sh'], stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        while True:
            line = proc.stdout.readline()
            if line.decode() != '':
                sys.stdout.write(line.decode())
            else:
                break

    def customReset(self):
        self.spinner.start()
        time.sleep(3)
        self.getMissingPackages()
        rapps = []

        if self.lineCount('apps-to-remove') > 0:
            self.getLocalUserList()
            self.getOldKernels()
            self.getLocalUserList()
            self.findNonDefaultUsers()
            with open('apps-to-remove', 'r') as atr:
                for line in atr:
                    rapps.append(line)
            self.spinner.stop()
            rapps.sort()
            opts = Picker(
                title='Custom Reset: Select packages to remove',
                options=rapps
            ).getSelected()
            if not opts:
                print("")
            else:
                path = 'custom-remove'
                mode = 'a' if self.isWritten else 'w'
                with open(path, mode) as f_out:
                    for item in opts:
                        f_out.write(item)
        else:
            print("All removable packages have already been removed, there are no more packages left")

    def getMissingPackages(self):
        self.getInstalledList()
        self.processManifest()
        try:
            if self.os_info['RELEASE'] == '17.3':
                word = "vivid"
            else:
                word = None
            black_list = (['linux-image', 'linux-headers', 'linux-generic', 'linux-kernel-generic',
                           'openjdk-7-jre', 'grub'])
            with open("apps-to-install", "w") as output, open("installed", "r") as installed, \
                    open(self.manifest, "r") as man:
                diff = set(man).difference(installed)
                for line in diff:
                    if word is not None and word in line:
                        black_list.append(line)
                    if not any(s in line for s in black_list):
                        output.writelines(line)
        except Exception as e:
            print(e.message)

    def save(self):
        self.getInstalledList()
        now = datetime.datetime.now()
        time = '{}{}{}'.format(now.hour, now.minute, now.second)
        name = 'snapshot - {}'.format(time)
        self.copy("installed", name)

    def removeOldKernels(self):
        self.getOldKernels()
        cache = apt.Cache(None)
        cache.open()
        try:
            with open('Kernels') as k:
                for pkg_name in k:
                    pkg = cache[pkg_name.strip()]
                    pkg.mark_delete(True, True)
            cache.commit()
        except subprocess.CalledProcessError as e:
            print(e.output)
        else:
            cache.close()

    def getOldKernels(self):
        try:
            results = subprocess.check_output(['bash', '/usr/lib/resetter-cli/data/scripts/remove-old-kernels.sh'])
            with open("Kernels", "w") as kernels:
                for line in results.splitlines():
                    kernels.writelines(line.decode() + '\n')
        except subprocess.CalledProcessError as e:
            print(e.output)

    def getInstalledList(self):
        try:
            result = subprocess.check_output(['dpkg', '--get-selections'])
            with open('installed', "w") as output:
                for line in result.splitlines():
                    p_line = line.decode().split('\t', 1)[0]
                    output.writelines(p_line + '\n')
        except subprocess.CalledProcessError as e:
            print(e.ouput)

    def processManifest(self):
        try:
            with open(self.manifest) as f, open('processed-manifest', 'w') as output:
                for line in f:
                    line = line.split('\t', 1)[0]
                    if line.endswith('\n'):
                        line = line.strip()
                    output.write(line + '\n')
            self.compareFiles()
        except Exception as e:
            print(e)

    def lineCount(self, file_path):
        x = open(file_path).readlines()
        line_count = len(x)
        return line_count

    def compareFiles(self):
        try:
            black_list = ('linux-image', 'linux-headers', 'linux-generic', 'ca-certificates', 'pyqt4-dev-tools',
                           'python-apt', 'python-aptdaemon', 'python-qt4', 'python-qt4-doc', 'libqt',
                           'pyqt4-dev-tools', 'openjdk', 'python-sip', 'gksu', 'grub', 'python-mechanize',
                           'python-bs4')
            with open('apps-to-remove', 'w') as output, open('installed', 'r') as installed, \
                    open(self.manifest, 'r') as pman:
                diff = set(installed).difference(pman)
                for line in diff:
                    if not any(s in line for s in black_list):
                        output.writelines(line)
        except Exception as e:
           print(e.message)

    def getLocalUserList(self):
        try:
            result = subprocess.check_output(['bash', '/usr/lib/resetter-cli/data/scripts/get-users.sh'])
            black_list = ['root']
            with open('users', 'w') as output:
                for line in result.splitlines():
                    line = line.decode()
                    if not any(s in line for s in black_list):
                        output.writelines(line + '\n')
        except (subprocess.CalledProcessError, Exception) as e:
            print("an error has occured while getting users, please check the log file {}".format(e))

    def findNonDefaultUsers(self):
        try:
            cmd = subprocess.check_output(['bash', '-c', 'compgen -u'])
            black_list = []
            with open(self.userlist, 'r') as userlist, open('users', 'r') as normal_users:
                for user in userlist:
                    black_list.append(user.strip())
                    for n_users in normal_users:
                        black_list.append(n_users.strip())
            with open('non-default-users', 'w') as output:
                for line in cmd.splitlines():
                    line = line.decode()
                    if not any(s in line for s in black_list):
                        self.non_defaults.append(line)
                        output.writelines(line + '\n')
        except (subprocess.CalledProcessError, Exception) as e:
            print("an error has occured while getting non-default users, please check the log file: {}".format(e))


if __name__ == '__main__':
    ResetterMenu().menu()
