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

def test_numdiff():
    sp = spec.SPEC('{"test": 100}')
    assert_true('test' in sp.diff(spec.SPEC('{"test": 101}')))
    assert_false('test' in sp.diff(spec.SPEC('{"test": 101}'), min_abs_numdiff=2))
    assert_true('test' in sp.diff(spec.SPEC('{"test": 102}'), min_abs_numdiff=2))
    assert_false('test' in sp.diff(spec.SPEC('{"test": 101}'), min_rel_numdiff=.1))
    assert_true('test' in sp.diff(spec.SPEC('{"test": 101}'), min_rel_numdiff=.01))
    # check sane behavior from 'fr' is 0
    sp = spec.SPEC('{"test": 0}')
    assert_false('test' in sp.diff(spec.SPEC('{"test": 1}'), min_abs_numdiff=2))
    assert_true('test' in sp.diff(spec.SPEC('{"test": 1}'), min_rel_numdiff=1.0))
    assert_true('test' in sp.diff(spec.SPEC('{"test": 1}'), min_rel_numdiff=0.00001))
    # arrays
    sp = spec.SPEC('{"test": [1,2,3,4]}')
    assert_true('numdiff' in sp.diff(spec.SPEC('{"test": [1,2,2,4]}'))['test'])
    assert_false('numdiff' in sp.diff(spec.SPEC('{"test": [1,2,3]}'))['test'])
    assert_false('numdiff' in sp.diff(spec.SPEC('{"test": [1,2,2,"hello"]}'))['test'])
