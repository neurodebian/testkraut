# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""""""

__docformat__ = 'restructuredtext'

from testkraut import utils
from testkraut.pkg_mngr import PkgManager
from nose.tools import *

def test_sysinfo():
    sysinfo = utils.describe_system()
    assert_true('python_version' in sysinfo)

def test_pkg_mngr():
    pkg = PkgManager()
    pypkgname = pkg.get_pkg_name('/usr/bin/python')
    print pkg.get_platform_name(), pypkgname
    if pkg.get_platform_name() in ('deb', 'rpm'):
        assert_false(pypkgname is None)
    pkg_info = pkg.get_pkg_info(pkg.get_pkg_name('/usr/bin/python'))
    print pkg_info

#def test_debian_stuff():
#    try:
#        import platform
#        dist = platform.linux_distribution()[0]
#        if not dist in ['debian']:
#            raise nose.SkipTest
#    except:
#        raise nose.SkipTest
#    # I hope that most systems have this...
#    assert_equal(utils.get_debian_pkgname('/etc/deluser.conf'), 'adduser')


