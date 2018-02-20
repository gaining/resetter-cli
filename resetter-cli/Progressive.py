#!/usr/bin/env python
# -*- coding: utf-8 -*-

import curses
import time
import textwrap
import subprocess
from dialog import Dialog


class ProgressBar(object):

    def update_progress(self, progress=None, status="", sig=5, response=None):
        screen = curses.initscr()
        screen.clear()
        self.response = response
        self.d = Dialog(dialog='dialog')

        maxY, maxX = screen.getmaxyx()
        self.window_height = maxY
        self.window_width = maxX

        curses.noecho()
        curses.cbreak()
        curses.curs_set(False);

        self.progress = progress
        self.main_screen = curses.newwin(self.window_height-3, self.window_width-3, 1, 1)

        self.custom_user_script = '/usr/lib/resetter-cli/data/scripts/custom_user.sh'
        self.default_user_script = '/usr/lib/resetter-cli/data/scripts/new-user.sh'
        self.no_show = False
        self.remaining = 0

        self.main_screen.border(0)
        self.main_screen.addstr(1, 1, "Working...")
        self.main_screen.addstr(6, 6, "Loading apps")
        self.main_screen.addstr(7, 6, "Removing packages")
        self.main_screen.addstr(8, 6, "Cleaning up")
        self.main_screen.addstr(9, 6, "Installing packages")
        self.main_screen.addstr(10, 6, "Deleting Users")
        self.main_screen.addstr(11, 6, "Finished")

        self.main_screen.box()
        self.main_screen.refresh()

        #ph = curses.newwin(12, 62, 13, 3)
        ph = curses.newwin(12, 60, 14, 3)

        ph.box()
        ph.refresh()
        #status_box = self.main_screen.derwin(10, 60, 13, 3)
        status_box = self.main_screen.derwin(10, 58, 14, 3)

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

        self.progressCheck(sig)
        self.cleanup(sig, status_box)

    def progressCheck(self, sig):  # Checks when to move to next step
        self.step(sig, 2)

    def cleanup(self, sig, sb):
        if sig == 7:
            with open('test.log', 'w') as f:
                proc = subprocess.Popen(['bash', '/usr/lib/resetter/data/scripts/fix-broken.sh'],
                                        stderr=subprocess.PIPE,
                                        stdout=subprocess.PIPE)
                while True:
                    line = proc.stdout.readline()
                    if line.decode() != '':
                        sb.clear()
                        sb.addstr(0, 0, textwrap.fill(line.decode(), 60))
                        sb.refresh()
                        f.write(line.decode())
                    else:
                        sig += 1
                        self.step(sig, 2)
                        self.installMissings(sig, sb)
                        break

    def installMissings(self, sig, sb):
        if sig == 8:
            sb.clear()
            sb.addstr(0, 0, textwrap.fill("Installing missing pacakges", 60))
            sb.refresh()
            subprocess.call(['/usr/bin/python3', '/usr/lib/resetter-cli/InstallMissing.py'])
            time.sleep(1)
            sig += 1
            self.step(sig, 2)
            self.removeUsers(sb, sig)

    def removeUsers(self, sb, sig):
        p = subprocess.check_output(['bash', 'custom-user-removals.sh'])
        sb.clear()
        sb.addstr(0, 0, textwrap.fill(str(p.decode()), 60))
        sb.refresh()
        self.addUsers(sb, sig)

    def addUsers(self, sb, sig):
        subprocess.call(['/usr/bin/python3', '/usr/lib/resetter-cli/Account.py', 'yes'])
        sb.clear()
        sig += 1
        self.step(sig, 2)
        sb.addstr(0, 0, textwrap.fill("Finished, press ESC to close", 60))
        sb.refresh()
        x = sb.getch()
        while x != 27:
            sb.refresh()
            x = sb.getch()
        curses.endwin()
        curses.endwin()
        subprocess.call(['/usr/bin/reset'])

    def step(self, y, x):
        arrow_status = self.main_screen.derwin(3, 4, y, x)
        arrow_status.standout()
        arrow_status.addstr(1, 1, '->')
        arrow_status.refresh()
        arrow_status.refresh()
        arrow_status.clear()

    def close(self):
        curses.endwin()


if __name__ == "__main__":
    ProgressBar().update_progress(50)
    time.sleep(3)
    ProgressBar().close()