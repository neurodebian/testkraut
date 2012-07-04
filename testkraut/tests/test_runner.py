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

from testkraut.spec import *
from testkraut.runner import *
from nose.tools import *

def test_run_cmd():
    # just very simple
    rt, out, err, merged = run_command('ls')
    assert_equal(rt, 0)
    assert_equal(err, '')
    assert(len(out) > 0)
    assert_equal(merged[0].split()[0], 'stdout')
