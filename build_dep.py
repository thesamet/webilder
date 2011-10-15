#!/usr/bin/env python
import gbp.deb as du
import os
import sys

DEB_VERSION = du.parse_changelog(filename="debian/changelog")["Version"]
BASE_VERSION = DEB_VERSION.split('-')[0]
print "Base version: %s" % BASE_VERSION

ORIG_FILENAME = '../webilder_%s.orig.tar.gz' % BASE_VERSION
if os.path.exists(ORIG_FILENAME):
    os.unlink(ORIG_FILENAME)
    print("Removed original tarball: %s" % ORIG_FILENAME)

if os.system('git-buildpackage --git-upstream-branch=master '
             '--git-upstream-tree=branch -us -uc') != 0:
    print "git-buildpackage failed"
    sys.exit(1)

os.rename(ORIG_FILENAME, '../Webilder-%s.tar.gz' % BASE_VERSION)
