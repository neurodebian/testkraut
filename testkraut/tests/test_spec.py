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
from nose.tools import *

def test_spec_io():
    assert_raises(ValueError, SPEC)
    # must have default version
    spec = SPEC(open('examples/demo_spec.json'))
    # no unknown keys
    assert_raises(ValueError, spec.__setitem__, 'mike', 0)

