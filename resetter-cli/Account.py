import sys
import time
from CustomApplyDialog import CustomApply
import subprocess
from dialog import Dialog
import os


class Account(object):
    diag = Dialog(dialog="dialog")

    def __init__(self):
        self.custom_user_script = '/usr/lib/resetter-cli/data/scripts/custom_user.sh'
        self.default_user_script = '/usr/lib/resetter-cli/data/scripts/new-user.sh'
        self.remaining = 0
        self.answer = sys.argv[1]
        self.response = False
        self.no_show = False
        if self.answer == 'add':
            self.answer = True
            self.addUser1()
        elif self.answer == 'yes':
            self.response = True
            self.addUser2(self.response)

    def addUser1(self):  # determine to add a backup user if all normal users are marked for deletion
        self.diag.set_background_title("Resetter-cli")
        if self.diag.yesno("Would you like to create a new user?") == self.diag.OK:
            while 1:
                self.answer = True
                self.username = self.diag.inputbox("What's your new  username?")
                self.password = self.diag.passwordbox("Please Enter {}'s new password?".format(self.username[1]),
                                                      insecure=True)

                if not self.complexityChecker(self.password[1]):
                    self.showMessage(self.diag)
                else:
                    with open(self.default_user_script, 'r') as f, open(self.custom_user_script, 'w') as out:
                        for line in f:
                            if line.startswith('PASSWORD'):
                                line = ("PASSWORD=""\'{}\'\n".format(self.password[1]))
                            if line.startswith('USERNAME'):
                                line = ("USERNAME=""\'{}\'\n".format(self.username[1]))
                            out.write(line)
                    CustomApply('remove-list', False, self.answer)
                    break
        else:  # checks to see if it is safe to skip adding a backup user, if it isn't it will add one.
            self.answer = False
            CustomApply('remove-list', False, self.answer)

    def showMessage2(self, response):
        self.diag.set_background_title("Resetter-cli")
        username = ''
        password = ''
        if response:
            with open(self.custom_user_script) as f:
                for line in f:
                    if line.startswith('PASSWORD'):
                        password = line.split('=')[-1].strip('"\'')
                    if line.startswith('USERNAME'):
                        username = line.split('=')[-1].strip('"\'')
            # if self.diag.yesno("Your username is: {}\npassword is: {}\n"
            #                    "Reboot required to apply changes, reboot now?"
            #                            .format(username, password)) == self.diag.OK:
            #     os.system('reboot')

            if self.diag.yesno("Your username is: "+ username+"\npassword is: "+password+
                                       "\nReboot required to apply changes, reboot now?",
                               height=10, width=40) == self.diag.OK:
                os.system('reboot')
            else:
                print('reboot canceled')
                pass
        else:
            if self.diag.infobox("Your username is default\n password is NewLife3!\n\n"
                              "Reboot required to apply changes, reboot now?", height=10, width=40):
                os.system('reboot')
            else:
                pass

    def addUser2(self, response):
        if response:
            subprocess.check_output(['bash', self.custom_user_script])
        else:  # if there are no remaining users, automatically create a backup user so you do not get locked out
            # even if you have chosen not to have one.
            with open('users') as u, open('custom-user-removals.sh') as du:
                converted_du = []
                for line in du:
                    line = line.split(' ')[-1]
                    converted_du.append(line)
                if len(converted_du) > 0:
                    diff = set(u).difference(converted_du)
                    i = len(diff)
                else:
                    i = len(u.read().strip().splitlines())
                self.remaining = i
                with open('pow', 'w') as a:
                    a.write(self.remaining)
            if self.remaining == 0:
                self.no_show = False
                subprocess.check_output(['bash', self.default_user_script])

        self.showMessage2(response)

    def complexityChecker(self, password):
        upper_count = 0
        num_count = 0
        good_length = False
        for s in password:
            if s.isupper():
                upper_count += 1
            if s.isdigit():
                num_count += 1
            if len(password) >= 8:
                good_length = True
        if upper_count < 1 or num_count < 1 or good_length is False:
            return False
        else:
            return True

    def showMessage(self, d):
        d.infobox("Password did not meet complexity requirements. "
                  "Make sure that your password contains:\n"
                  "At least 8 characters\n"
                  "At least one number\n"
                  "At least one uppercase letter")
        time.sleep(2.3)


if __name__ == '__main__':
    Account()
