#!/usr/bin/python
import curses
import subprocess
import apt
import os
import textwrap
import time
from Account import Account
import sys


class Picker(object):
    """Allows you to select from a list with curses"""

    def __init__(self, options, title='', arrow="-->",
                 footer="s = Select/Deselect, d = Description, q = Cancel, -> Next, <- Previous",
                 checkall=False,
                 mut=False,
                 more="...",
                 border="||--++++",
                 c_selected="(x)",
                 c_empty="( )"):

        self.title = title
        self.arrow = arrow
        self.footer = footer
        self.more = more
        self.border = border
        self.c_selected = c_selected
        self.c_empty = c_empty
        self.checkall = checkall
        self.immutable = mut
        self.backup1 = []
        self.backup2 = []
        self.page = 1
        self.is_usermode = False
        self.user_removal = []
        self.position = 0
        self.cache = apt.Cache(None)
        self.cache.open()
        self.screen = None
        self.win = None
        self.cursor = 0
        self.offset = 0
        self.selected = 0
        self.selcount = 0
        self.aborted = False
        self.length = 0
        self.all_options = []
        # subprocess.call(['/usr/bin/resize', '-s', '34', '107'], stderr=subprocess.STDOUT)

        command = ['/usr/bin/resize', '-s', '34', '107']
        with open(os.devnull, "w") as null:
            subprocess.call(command, stdout=null, stderr=null)

        for option in options:
            self.all_options.append({
                "label": option,
                "selected": checkall,
                'home_del': False

            })
            self.length = len(self.all_options)
        self.backup0 = self.all_options[:]
        self.b_title = self.title[:]

        self.curses_start()
        curses.wrapper(self.curses_loop)
        self.curses_stop()

    def missingsList(self, options=None):
        del self.all_options[:]
        options = open('apps-to-install').read().splitlines()
        for option in options:
            self.all_options.append({
                "label": option + '\n',
                "selected": self.checkall,
                'home_del': False

            })
            self.length = len(self.all_options)
        self.backup1 = self.all_options[:]
        self.cursor = 0

        self.curses_start()
        curses.wrapper(self.curses_loop)
        self.curses_stop()

    def usersList(self, options=None):
        del self.all_options[:]
        users1 = open('users').read().splitlines()
        users2 = open('non-default-users').read().splitlines()
        for item in users1:
            self.all_options.append({
                "label": item + '\n',
                "selected": self.checkall,
                'home_del': False,
                'count': 0
            })
        for ndu in users2:
            self.all_options.append({
                "label": ndu + '\n',
                "selected": self.checkall,
                'home_del': False,
                'count': 0
            })

            self.length = len(self.all_options)
        self.backup2 = self.all_options[:]
        self.cursor = 0

        self.curses_start()
        curses.wrapper(self.curses_loop)
        self.curses_stop()

    def curses_loop(self, stdscr):

        while not self.aborted:  # draws 1st menu
            try:
                self.redraw()
                c = stdscr.getch()
                if c == ord('q') or c == ord('Q') or c == 27:
                    self.aborted = True

                elif c == curses.KEY_UP:
                    self.cursor -= 1

                elif c == curses.KEY_LEFT:
                    self.page -= 1
                    if self.page < 1:
                        self.page = 1
                    self.switchPages()

                elif c == curses.KEY_RIGHT:
                    self.page += 1
                    if self.page > 4:
                        self.page = 4
                    self.outputSelected(self.fName())
                    self.switchPages()
                elif self.page == 4:
                    self.a = Account()
                    #self.startProgress()
                    #self.aborted = True

                elif c == ord('d'):
                    if self.page == 1 or self.page == 2:
                        pkg = self.cache[str(self.all_options[self.selected]['label']).strip()]
                        text = pkg.versions[0].raw_description
                        self.description(text)

                elif c == curses.KEY_DOWN:
                    self.cursor += 1

                elif c == ord('s') and not self.immutable:
                    if not self.is_usermode:
                        self.all_options[self.selected]['selected'] = not self.all_options[self.selected]['selected']
                    else:
                        self.position = 'userdel -f {}'.format(self.all_options[self.selected]['label'])
                        self.position2 = 'userdel -rf {}'.format(self.all_options[self.selected]['label'])
                        self.all_options[self.selected]['count'] += 1
                        if self.all_options[self.selected]['count'] > 2:
                            self.all_options[self.selected]['count'] = 0
                        self.userMode()

                elif c == ord('s') and self.immutable:
                    pass
            except IndexError:
                pass

            self.check_cursor_up()
            self.check_cursor_down()
            # compute selected position only after dealing with limits
            self.selected = self.cursor + self.offset
            temp = self.getSelected()
            if not self.aborted:
                self.selcount = len(temp)
            else:
                break

    def userMode(self):
        if self.is_usermode:
            if self.all_options[self.selected]['count'] == 1:
                self.all_options[self.selected]['selected'] = True
                self.user_removal.append('userdel -f {}'.format(self.all_options[self.selected]['label']))
            elif self.all_options[self.selected]['count'] == 2:
                self.all_options[self.selected]['home_del'] = True
                del self.user_removal[self.user_removal.index(self.position)]
                self.user_removal.append('userdel -rf {}'.format(self.all_options[self.selected]['label']))
            elif self.all_options[self.selected]['count'] == 0:
                self.all_options[self.selected]['selected'] = False
                self.all_options[self.selected]['home_del'] = False
                del self.user_removal[self.user_removal.index(self.position2)]
        else:
            pass

    def switchPages(self):
        # switches to first page
        if self.page == 1:
            self.footer = "s = Select/Deselect, d = Description, q = Cancel, -> Next, <- Previous"
            self.is_usermode = False
            self.arrow = '-->'
            if len(self.all_options) != len(self.backup0):
                self.all_options = self.backup0[:]
                self.title = self.b_title[:]
                self.length = len(self.all_options)

        # switches to second page
        elif self.page == 2:
            self.is_usermode = False
            self.arrow = '-->'
            self.title = "Select packages to install"
            self.footer = "s = Select/Deselect, d = Description, q = Cancel, -> Next, <- Previous"
            self.offset = 0
            self.cursor = 0
            if len(self.backup1) > 0:
                self.all_options = self.backup1[:]
                self.length = len(self.all_options)
            else:
                self.missingsList()

        # switches to third page
        elif self.page == 3:
            self.is_usermode = True
            self.arrow = '-->'
            self.title = "Select users to Delete"
            self.footer = "s = Remove User or Remove User+HomeDir, q = Cancel, -> Next, <- Previous"
            self.offset = 0
            self.cursor = 0
            if len(self.backup2) > 0:
                self.all_options = self.backup2[:]
                self.length = len(self.all_options)
            else:
                self.usersList()

        # switches to fourth page
        elif self.page == 4:
            self.curses_stop()
            self.aborted = True
            self.a = Account()
            self.a.addUser1()


    def fName(self):
        if self.page == 1:
            page_title = 'custom-remove'
        elif self.page == 2:
            page_title = 'custom-remove'
        elif self.page == 3:
            page_title = 'custom-install'
        elif self.page == 4:
            page_title = 'custom-user-removals'
        return page_title

    def outputSelected(self, output_file):
        opts = self.getSelected() if not self.is_usermode else self.user_removal
        with open(output_file, 'w') as f_out:
            for item in opts:
                f_out.write(item)

    def description(self, text):
        box1 = curses.newwin(20, 40, 6, 50)
        box2 = box1.derwin(18, 38, 1, 1)
        box2.scrollok(1)
        box1.immedok(True)
        box2.immedok(True)
        box1.box()
        box2.addstr(1, 0, textwrap.fill(text, 70))
        self.screen.getch()

    def curses_start(self):
        self.screen = curses.initscr()
        maxY, maxX = self.screen.getmaxyx()
        self.window_height = maxY - 10
        self.window_width = maxX - 10
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0);
        self.win = curses.newwin(5 + self.window_height, self.window_width, 2, 4)

    def curses_stop(self):
        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()

    def getSelected(self):
        if self.aborted:
            return False
        ret_s = filter(lambda x: x['selected'], self.all_options)
        ret = map(lambda x: x['label'], ret_s)
        return ret

    def redraw(self):
        self.win.clear()
        self.win.border(
            self.border[0], self.border[1],
            self.border[2], self.border[3],
            self.border[4], self.border[5],
            self.border[6], self.border[7]
        )
        self.win.addstr(0, 5, " " + self.title + " ")
        self.win.addstr(self.window_height + 4, 5, " " + self.footer + " ")
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

        position = 0
        range = self.all_options[self.offset:self.offset + self.window_height + 1]
        for option in range:
            if option['selected']:
                line_label = self.c_selected + " "
            else:
                line_label = self.c_empty + " "
            if option['selected'] and option['home_del']:
                self.win.addstr(position + 2, 9, option['label'])
                self.win.addstr(position + 2, 5, line_label, curses.color_pair(1))
            else:
                self.win.addstr(position + 2, 5, line_label + option['label'])
            position += 1

        # hint for more content above
        if self.offset > 0:
            self.win.addstr(1, 5, self.more)

        # hint for more content below
        if self.offset + self.window_height <= self.length - 2:
            self.win.addstr(self.window_height + 3, 5, self.more)

        self.win.addstr(
            0, self.window_width - 8,
               " " + str(self.selcount) + "/" + str(self.length) + " "
        )
        self.win.addstr(self.cursor + 2, 1, self.arrow)
        self.win.refresh()

    def check_cursor_up(self):
        if self.cursor < 0:
            self.cursor = 0
            if self.offset > 0:
                self.offset -= 1

    def check_cursor_down(self):
        if self.cursor >= self.length:
            self.cursor -= 1

        if self.cursor > self.window_height:
            self.cursor = self.window_height
            self.offset += 1

            if self.offset + self.cursor >= self.length:
                self.offset -= 1
