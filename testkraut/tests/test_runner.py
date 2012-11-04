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

from testkraut import spec
from testkraut import runner
from testkraut import utils
from nose.tools import *

def test_run_cmd():
    # just very simple
    res = utils.run_command('ls')
    rt = res['retval']
    assert_equal(rt, 0)
    assert_equal(len(res['stderr']), 0)
    assert(len(res['stdout']) > 0)
    assert_equal(res['merged'][0].split()[0], 'stdout')

def test_debian_stuff():
    try:
        import platform
        dist = platform.linux_distribution()[0]
        if not dist in ['debian']:
            raise SkipTest
    except:
        raise SkipTest
    # I hope that most systems have this...
    assert_equal(utils.get_debian_pkgname('/etc/deluser.conf'), 'adduser')
