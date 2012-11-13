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

import os
from os.path import join as opj
from testkraut import utils
from testkraut.pkg_mngr import PkgManager
from nose.tools import *
from testkraut.tests.test_runner import with_tempdir

def test_sysinfo():
    sysinfo = utils.describe_system()
    assert_true('python_version' in sysinfo)

def test_pkg_mngr():
    pkg = PkgManager()
    pypkgname = pkg.get_pkg_name('/usr/bin/python')
    if pkg.get_platform_name() in ('deb', 'rpm'):
        assert_false(pypkgname is None)
    pkg_info = pkg.get_pkg_info(pkg.get_pkg_name('/usr/bin/python'))

@with_tempdir()
def test_strace_wrapper(wdir):
    curdir = os.path.realpath(os.curdir)
    try:
        os.chdir(wdir)
        inf_path = opj(wdir, 'inf')
        outf_path = opj(wdir, 'outf')
        inf = open(inf_path, 'w')
        inf.write('TEST')
        inf.close()
        cmd = ['python', '-c', 'open(\"%s\",\"w\").write(open(\"%s\").read())'
                               % (outf_path, inf_path)]
        procs, retval = utils.get_cmd_prov_strace(cmd)
        assert_equal(retval, 0)
        assert_equal(len(procs), 1)
        assert_equal(procs.keys(), ['mother'])
        exe = procs['mother']
        assert_equal(exe['uses'], set(['inf']))
        assert_equal(exe['generates'], set(['outf']))
        assert_equal(exe['started_by'], None)
    finally:
        os.chdir(curdir)

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


