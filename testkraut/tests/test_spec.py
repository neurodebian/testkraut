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
from nose.tools import *
import pkgutil

def test_spec_io():
    assert_raises(ValueError, spec.SPEC)
    # must have default version
    sp = spec.SPEC(pkgutil.get_data('testkraut', 'library/demo/spec.json'))
    # no unknown keys
    assert_raises(ValueError, sp.__setitem__, 'mike', 0)
    # from a str
    sp = spec.SPEC('{"test":{"command":["uname"],"type":"shell_command"}}')
