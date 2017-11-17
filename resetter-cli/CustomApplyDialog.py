#!/usr/bin/env python
# -*- coding: utf-8 -*-

import apt
import apt.package
import curses

from AptProgress import UIAcquireProgress, UIInstallProgress
from Progressive import ProgressBar
import textwrap


class CustomApply():
    """Allows you to select from a list with curses"""

    def __init__(self, f_name, action, answer):
        self.win = None
        self.screen = curses.initscr()
        self.aprogress = UIAcquireProgress(6)
        self.iprogress = UIInstallProgress(6)
        self.response = answer
        self.cache = apt.Cache(None)
        self.cache.open()
        self.percent = ''
        self.load(f_name, action)

    def curses_start(self):
        maxY, maxX = self.screen.getmaxyx()
        self.window_height = maxY
        self.window_width = maxX
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0);
        self.win = curses.newwin(self.window_height, self.window_width, 2, 4)

    def curses_stop(self):
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()

    def line_count(self, file_path):
        n = open(file_path).readlines()
        line_count = len(n)
        return line_count

    def load(self, f_name, action):
        self.curses_start()
        loading = 0
        x = float(100) / self.line_count(f_name) if self.line_count(f_name) != 0 else 0
        p = ProgressBar()
        with open(f_name) as packages:
            for pkg_name in packages:
                try:
                    loading += x
                    pkg = self.cache[pkg_name.strip()]
                    if action and not pkg.is_installed:
                        pkg.mark_install()
                        p.update_progress(int(loading))
                    else:
                        pkg.mark_delete(True, True)
                        p.update_progress(int(loading), sig=5)
                except (KeyError, SystemError) as error:
                    if pkg.is_inst_broken or pkg.is_now_broken:
                        continue
        self.performActions()

    def performActions(self):
        self.cache.commit(self.aprogress, self.iprogress)
        self.curses_stop()


if __name__ == '__main__':
    CustomApply('custom-install2', False, False)
