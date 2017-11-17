from dialog import Dialog
import sys
import time
from CustomApplyDialog import CustomApply
import subprocess

class Account(object):

    def __init__(self):
        self.custom_user_script = '/usr/lib/resetter/data/scripts/custom_user.sh'
        self.default_user_script = '/usr/lib/resetter/data/scripts/new-user.sh'
        self.no_show = False
        self.remaining = 0
        self.answer = False
        self.d = Dialog(dialog="dialog")


    def addUser1(self):  # determine to add a backup user if all normal users are marked for deletion
        self.d.set_background_title("Resetter-cli")
        if self.d.yesno("Would you like to create a new user?") == self.d.OK:
            while 1:
                self.answer = True
                self.username = self.d.inputbox("What's your new  username?")
                self.password = self.d.passwordbox("Please Enter {}'s new password?".format(self.username[1]), insecure=True)

                if not self.complexityChecker(self.password[1]):
                    self.showMessage(self.d)
                    time.sleep(2.3)
                else:
                    with open(self.default_user_script, 'r') as f, open(self.custom_user_script, 'w') as out:
                        for line in f:
                            if line.startswith('PASSWORD'):
                                line = ("PASSWORD=""\'{}\'\n".format(self.password[1]))
                            if line.startswith('USERNAME'):
                                line = ("USERNAME=""\'{}\'\n".format(self.username[1]))
                            out.write(line)
                    CustomApply('custom-install2', False, self.answer)
                    break
        else:
            self.answer = False
            with open('users') as u, open('custom-users-to-delete.sh') as du:
                converted_du = []
                i = 0
                for line in du:
                    line = line.split(' ')[-1]
                    converted_du.append(line)
                if len(converted_du) > 0:
                    diff = set(u).difference(converted_du)
                    for x in diff:
                        i += 1
                else:
                    i = len(u.read().strip().splitlines())
                self.remaining = i
            CustomApply('remove-list', False, self.answer)

    def showMessage2(self):
        if self.answer:
            self.d.infobox("Your username is {}, password is {}".format(self.username[1], self.password[1]))
        else:
            self.d.infobox("Your username is default, password is NewLife3!")

    def addUser2(self):
        if self.answer:
            p = subprocess.check_output(['bash', self.custom_user_script])
        else:  # if there are no remaining users, automatically create a backup user so you do not get locked out
            # even if you have chosen not to have one.
            if self.remaining == 0:
                p = subprocess.check_output(['bash', self.default_user_script])

    def getUsername(self):
        return self.username

    def getPassword(self):
        return self.password

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
        time.sleep(3)


if __name__ == '__main__':
    Account()
