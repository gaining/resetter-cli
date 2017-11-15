#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses
import time
import textwrap
import subprocess
import sys
#from Account import Account
from dialog import Dialog
import os

class ProgressBar(object):

    def update_progress(self, progress=None, status="", sig=None, response=False):
        screen = curses.initscr()
        screen.clear()
        self.response = response
        self.d = Dialog(dialog="dialog")


        maxY, maxX = screen.getmaxyx()
        self.window_height = maxY
        self.window_width = maxX

        curses.noecho()
        curses.cbreak()
        curses.curs_set(False);

        self.progress = progress
        self.main_screen = curses.newwin(self.window_height-3, self.window_width-3, 1, 1)

        self.custom_user_script = '/usr/lib/resetter/data/scripts/custom_user.sh'
        self.default_user_script = '/usr/lib/resetter/data/scripts/new-user.sh'
        self.no_show = False
        self.remaining = 0
        #self.accounts = Account()

        self.main_screen.border(0)
        self.main_screen.addstr(1, 1, "Working...")
        self.main_screen.addstr(6, 6, "Loading apps")
        self.main_screen.addstr(7, 6, "Removing packages")
        self.main_screen.addstr(8, 6, "Cleaning up")
        self.main_screen.addstr(9, 6, "Installing packages")
        self.main_screen.addstr(10, 6,"Deleting Users")

        self.main_screen.box()
        self.main_screen.refresh()

        ph = curses.newwin(12, 62, 13, 3)
        ph.box()
        ph.refresh()
        status_box = self.main_screen.derwin(10, 60, 13, 3)
        status_box.scrollok(True)

        win = self.main_screen.derwin(3, 36, 3, 2)
        win.border(0)

        rangex = (30/float(100)) * self.progress

        pos = int(rangex)
        display = '#'
        if pos != 0:  # code for status and progress display
            win.addstr(1, 1, "{}".format(display * pos))
            win.addstr(1, 31, "{}%".format(self.progress))
            status_box.addstr(0, 0, textwrap.fill(status, 60))
            status_box.refresh()
            win.refresh()

        self.progressCheck(int(sig))
        self.cleanup(sig, status_box, win)

    def progressCheck(self, sig):  # Checks when to move to next step
        self.step(sig, 2)

    def cleanup(self, sig, sb, win):
        if sig == 7:
            with open('test.log', 'w') as f:
                process = subprocess.Popen(['bash', '/usr/lib/resetter/data/scripts/fix-broken.sh'],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for line in iter(process.stdout.readline, ''):
                    sb.addstr(0, 0, textwrap.fill(line, 60))
                    sb.refresh()
                    f.write(line)
                sig += 1
                self.step(sig, 2)
                time.sleep(1.3)
                self.installMissings(sig, sb)

    def installMissings(self, sig, sb):
        if sig == 8:
            sb.clear()
            sb.addstr(0, 0, textwrap.fill("Installing missing pacakges", 60))
            sb.refresh()
            #Code for action
            time.sleep(1)
            sig += 1
            self.step(sig, 2)
            self.addUsers(sb)

    def addUsers(self, sb):
        self.addUser2()
        sb.clear()
        sb.addstr(0, 0, textwrap.fill("Finished, press ESC to close", 60))
        sb.refresh()
        self.showMessage2()
        time.sleep(2)
        x = sb.getch()
        while x != 27:
            sb.refresh()
            x = sb.getch()
        curses.endwin()
        curses.endwin()

    def showMessage2(self):
        self.d.set_background_title("Resetter-cli")
        username = ''
        password = ''
        if self.response:
            with open(self.custom_user_script) as f:
                for line in f:
                    if 'PASSWORD' in line:
                        password = line.split('=')[-1]
                    if 'USERNAME' in line:
                        username = line.split('=')[-1]
            self.d.infobox("Your username is {}, password is {}".format(username, password))
        else:
            self.d.infobox("Your username is default, password is NewLife3!")

    def addUser2(self):
        if self.response:
            p = subprocess.check_output(['bash', self.custom_user_script])
        else:  # if there are no remaining users, automatically create a backup user so you do not get locked out
            # even if you have chosen not to have one.
            if self.remaining == 0:
                p = subprocess.check_output(['bash', self.default_user_script])

    def reboot(self):
        if self.d.yesno("Reboot required to apply changes, reboot now? ") == self.d.OK:
            os.system('reboot')
        else:
            pass

    def removeUsers(self, sb):
        p = subprocess.check_output(['bash', 'custom-users-to-delete.sh'])
        sb.clear()
        sb.addstr(0, 0, textwrap.fill(str(p), 60))
        sb.refresh()
        time.sleep(1)
        self.addUsers()

    def step(self, y, x):
        arrow_status = self.main_screen.derwin(3, 4, y, x)
        arrow_status.standout()
        arrow_status.addstr(1, 1, '->')
        arrow_status.refresh()
        # self.blink(arrow_status)
        arrow_status.refresh()
        arrow_status.clear()
        # time.sleep(0.3)

    def blink(self, win):  # need to implement different thread for blinking
        win.standend()
        win.addstr(1, 1, '  ')
        win.refresh()
        time.sleep(0.5)

    def close(self):
        curses.endwin()

if __name__ == '__main__':
    ProgressBar().update_progress(50)
    ProgressBar().close()