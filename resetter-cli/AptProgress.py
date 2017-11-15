#!/usr/bin/python
import os
from apt.progress.base import InstallProgress, OpProgress, AcquireProgress
import apt_pkg
from Progressive import ProgressBar

apt_pkg.init_config()
apt_pkg.config.set('DPkg::Options::', '--force-confnew')
apt_pkg.config.set('APT::Get::Assume-Yes', 'true')
apt_pkg.config.set('APT::Get::force-yes', 'true')
os.putenv('DEBIAN_FRONTEND', 'gnome')


class UIOpProgress(OpProgress):
    def __init__(self):
        OpProgress.__init__(self)

    def update(self, percent):
        OpProgress.update(self, percent)

    def done(self):
        OpProgress.done(self)


class UIAcquireProgress(AcquireProgress):
    def __init__(self):
        AcquireProgress.__init__(self)
        self.percent = 0.0
        self.a = ProgressBar()
        self.other = False
        self.sig = 6

    def pulse(self, owner):
        current_item = self.current_items + 1
        if current_item > self.total_items:
            current_item = self.total_items
        if self.other:
            status = "Updating source {} of {}".format(current_item, self.total_items)
            percent = (float(self.current_items) / self.total_items) * 100

        else:
            if self.current_cps == 0:
                status = "Downloading package {} of {} at - MB/s".format(current_item, self.total_items)
            else:
                status = "Downloading package {} of {} at {:.2f} MB/s".format(current_item, self.total_items,
                                                                              (float(self.current_cps) / 10 ** 6))
            percent = (((self.current_bytes + self.current_items) * 100.0) /
                       float(self.total_bytes + self.total_items))
        self.a.update_progress(int(percent), status=status, sig=self.sig)
        return True

    def stop(self):
        self.a.update_progress(progress=100, sig=self.sig)

    def done(self, item):
        pass
        # print "{} [Downloaded]".format(item.shortdesc)

    def fail(self, item):
        pass
        # print "{} Failed".format(item.shortdesc)

    def ims_hit(self, item):
        pass
        # print "{} [Hit]".format(item.shortdesc)


class UIInstallProgress(InstallProgress):
    def __init__(self):
        InstallProgress.__init__(self)
        self.last = 0.0
        self.b = ProgressBar()
        self.step = 6

    def fork(self):
        pid = os.fork()
        if pid == 0:
            logfd = os.open('dpkg.log', os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o644)
            os.dup2(logfd, 1)
            os.dup2(logfd, 2)
        return pid

    def status_change(self, pkg, percent, status):
        super(InstallProgress, self).__init__()
        if self.last >= percent:
            return
        self.last = percent
        self.b.update_progress(int(percent), status=status + str(pkg), sig=self.step)

    def pulse(self):
        return InstallProgress.pulse(self)

    def finish_update(self):
        self.step += 1
        self.b.update_progress(100, status="Finished", sig=self.step)

    def processing(self, pkg, stage):
        self.b.update_progress(status="starting {} stage for {}".format(stage, pkg))

    def dpkg_status_change(self, pkg, status):
        self.b.update_progress(status="{} {}".format(status, pkg))

    def conffile(self, current, new):
        self.b.update_progress(status='automatically accepted new config file')

    def error(self, errorstr):
        self.b.update_progress(status="ERROR: {}".format(errorstr))
