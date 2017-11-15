#!/usr/bin/python
import lsb_release
from SetEnvironment import Settings
from termcolor import colored
from picker import Picker
from Spinner import Spinner
import os
import sys
import subprocess
import datetime
import apt

class ResetterMenu(object):
    def __init__(self, parent=None):
        print("Resetter-cli v1.0.0\n")
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
        # self.detectRoot()

    def menu(self):
        while self.loop:  # While loop which will keep going until loop = False
            print("1. Automatic Reset")
            print("2. Custom Reset")
            print("3. Fix Broken Packages")
            print("4. Remove Old Kernels")
            print("5. About")
            print("6. Exit")
            try:
                choice = int(raw_input("Choose an option [1-6]: "))
                if choice == 1:
                    self.autoReset()

                elif choice == 2:
                    self.customReset()

                elif choice == 3:
                    self.fixBroken()

                elif choice == 4:
                    self.removeOldKernels()

                elif choice == 6:
                    print("Goodbye")
                    self.loop = False
                else:
                    print("Invalid Choice\n")
            except ValueError:
                print("Invalid Choice\n")

    def autoReset(self):
        yes = set(['yes', 'y', ''])
        no = set(['no', 'n'])
        choice = raw_input(colored("This will reset your " + str(self.os_info['DESCRIPTION']) +
                                   " installation to its factory defaults. "
                                   "Local user accounts and all their contents will also be removed. "
                                   "Are you sure you'd like to continue?: ",
                               'yellow')).lower()
        if choice.lower() in yes:
            print("yes chosen")
            rapps = []
            self.spinner.start()
            self.getMissingPackages()
            if self.lineCount("apps-to-remove") > 0:
                self.getLocalUserList()
                self.findNonDefaultUsers()
                with open('apps-to-remove') as atr:
                    for line in atr:
                        rapps.append(line)
                self.spinner.stop()
                opts = Picker(
                    title='Automatic Reset: All of these packages will be removed',
                    options=rapps,
                    checkall=True,
                    mut=True
                ).getSelected()
                if not opts:
                    print("")
            else:
                print("All removable packages have already been removed, there are no more packages left")
        elif choice.lower() in no:
            pass
        else:
            print("Please respond with 'yes' or 'no'")

    def fixBroken(self):
        with open('test.log', 'w') as f:
            process = subprocess.Popen(['bash', '/usr/lib/resetter/data/scripts/fix-broken.sh'],
                                       stdout=subprocess.PIPE,  stderr=subprocess.PIPE)
            for line in iter(process.stdout.readline, ''):
                    sys.stdout.write(line)
                    f.write(line)

    def customReset(self):
        self.spinner.start()
        rapps = []
        self.getMissingPackages()

        if self.lineCount("apps-to-remove") > 0:
            self.getLocalUserList()
            self.getOldKernels()
            self.getLocalUserList()
            self.findNonDefaultUsers()
            with open('apps-to-remove') as atr:
                for line in atr:
                    rapps.append(line)
            self.spinner.stop()
            opts = Picker(
                title='Custom Reset: Select packages to remove',
                options=rapps
            ).getSelected()
            if not opts:
                print("")
            else:
                path = "custom-remove"
                mode = 'a' if self.isWritten else 'w'
                with open(path, mode) as f_out:
                    for item in opts:
                        f_out.write(item)
        else:
            print("All removable packages have already been removed, there are no more packages left")

    def findNonDefaultUsers(self):
        try:
            cmd = subprocess.check_output(['bash', '-c', 'compgen -u'])
            black_list = []
            self.non_defaults = []
            with open(self.userlist, 'r') as userlist, open('users', 'r') as normal_users:
                for user in userlist:
                    black_list.append(user.strip())
                    for n_users in normal_users:
                        black_list.append(n_users.strip())
            with open('non-default-users', 'w') as output:
                for line in cmd.splitlines():
                    if not any(s in line for s in black_list):
                        self.non_defaults.append(line)
                        output.writelines(line + '\n')
        except (subprocess.CalledProcessError, Exception) as e:
            print("an error has occured while getting users, please check the log file: {}".format(e))

    def getMissingPackages(self):
        self.getInstalledList()
        self.processManifest()
        try:
            cmd = subprocess.Popen(['grep', '-vxf', 'installed', 'processed-manifest'], stderr=subprocess.STDOUT,
                                   stdout=subprocess.PIPE)
            cmd.wait()
            result = cmd.stdout
            if self.os_info['RELEASE'] == '17.3':
                word = "vivid"
            else:
                word = None
            black_list = ['linux-image', 'linux-headers', "openjdk-7-jre"]
            with open('apps-to-install', 'w') as output:
                for line in result:
                    if word is not None and word in line:
                        black_list.append(line)
                    if not any(s in line for s in black_list):
                        output.writelines(line)
        except (subprocess.CalledProcessError, Exception) as e:
            print(e.ouput)

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
        except (subprocess.CalledProcessError) as e:
            print(e.output)
        else:
            cache.close()

    def getOldKernels(self):
        try:
            cmd = subprocess.Popen(['bash', '/usr/lib/resetter/data/scripts/remove-old-kernels.sh'],
                                   stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            cmd.wait()
            results = cmd.stdout
            with open("Kernels", "w") as kernels:
                for line in results:
                    kernels.writelines(line)
        except subprocess.CalledProcessError as e:
            print(e.output)

    def getInstalledList(self):
        try:
            p1 = subprocess.Popen(['dpkg', '--get-selections'], stdout=subprocess.PIPE, bufsize=1)
            result = p1.stdout
            with open("installed", "w") as output:
                for line in result:
                    tab = '\t'
                    p_line = str(line).split(tab, 1)[0]
                    output.writelines(p_line + '\n')
        except subprocess.CalledProcessError as e:
            print(e.ouput)

    def processManifest(self):
        try:
            with open(self.manifest) as f, open("processed-manifest", "w") as output:
                for line in f:
                    tab = '\t'
                    line = line.split(tab, 1)[0]
                    if line.endswith('\n'):
                        line = line.strip()
                    output.write(line + '\n')
            self.compareFiles()
        except Exception as e:
            print(e)

    def lineCount(self, f_in):
        p = subprocess.Popen(['wc', '-l', f_in], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        result, err = p.communicate()
        if p.returncode != 0:
            raise IOError(err)
        return int(result.strip().split()[0])

    def compareFiles(self):
        try:
            cmd = subprocess.Popen(['grep', '-vxf', 'processed-manifest', 'installed'], stderr=subprocess.STDOUT,
                                   stdout=subprocess.PIPE)
            cmd.wait()
            result = cmd.stdout
            black_list = ['linux-image', 'linux-headers', 'ca-certificates', 'pyqt4-dev-tools',
                          'python-apt', 'python-aptdaemon', 'python-qt4', 'python-qt4-doc', 'libqt',
                          'pyqt4-dev-tools', 'openjdk', 'python-sip', 'snap', 'gksu', 'resetter', 'python-bs4']
            with open("apps-to-remove", "w") as output:
                for line in result:
                    if not any(s in line for s in black_list):
                        output.writelines(line)
        except (subprocess.CalledProcessError, Exception) as e:
            pass

    def getLocalUserList(self):
        try:
            cmd = subprocess.Popen(['bash', '/usr/lib/resetter/data/scripts/get-users.sh'], stderr=subprocess.STDOUT,
                                   stdout=subprocess.PIPE)
            cmd.wait()
            result = cmd.stdout
            black_list = ['root']
            with open("users", "w") as output:
                for line in result:
                    if not any(s in line for s in black_list):
                        output.writelines(line)
        except (subprocess.CalledProcessError, Exception) as e:
            print("an error has occured while getting users, please check the log file {}".format(e))


if __name__ == '__main__':
    ResetterMenu().menu()
