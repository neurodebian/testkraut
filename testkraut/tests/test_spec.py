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
    sp = spec.SPEC('{"tests":[{"command":["uname"],"type":"shell"}]}')

def test_numdiff():
    sp = spec.SPEC('{"tests": 100}')
    assert_true('tests' in sp.diff(spec.SPEC('{"tests": 101}')))
    assert_false('tests' in sp.diff(spec.SPEC('{"tests": 101}'), min_abs_numdiff=2))
    assert_true('tests' in sp.diff(spec.SPEC('{"tests": 102}'), min_abs_numdiff=2))
    assert_false('tests' in sp.diff(spec.SPEC('{"tests": 101}'), min_rel_numdiff=.1))
    assert_true('tests' in sp.diff(spec.SPEC('{"tests": 101}'), min_rel_numdiff=.01))
    # check sane behavior from 'fr' is 0
    sp = spec.SPEC('{"tests": 0}')
    assert_false('tests' in sp.diff(spec.SPEC('{"tests": 1}'), min_abs_numdiff=2))
    assert_true('tests' in sp.diff(spec.SPEC('{"tests": 1}'), min_rel_numdiff=1.0))
    assert_true('tests' in sp.diff(spec.SPEC('{"tests": 1}'), min_rel_numdiff=0.00001))
    # arrays
    sp = spec.SPEC('{"tests": [1,2,3,4]}')
    assert_true('numdiff' in sp.diff(spec.SPEC('{"tests": [1,2,2,4]}'))['tests'])
    assert_false('numdiff' in sp.diff(spec.SPEC('{"tests": [1,2,3]}'))['tests'])
    assert_false('numdiff' in sp.diff(spec.SPEC('{"tests": [1,2,2,"hello"]}'))['tests'])
