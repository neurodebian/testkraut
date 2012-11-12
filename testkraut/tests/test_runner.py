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

import tempfile
import shutil
import os
from os.path import join as opj
from testkraut import spec
from testkraut import runner
from testkraut import utils
from nose.tools import *
import nose

def with_tempdir(*targs, **tkwargs):
    def decorate(func):
        def newfunc(*arg, **kwargs):
            import tempfile
            wdir = tempfile.mkdtemp(*targs, **tkwargs)
            try:
                func(*((wdir,) + arg), **kwargs)
            finally:
                import shutil
                shutil.rmtree(wdir)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate

def test_run_cmd():
    # just very simple
    res = utils.run_command('ls')
    rt = res['retval']
    assert_equal(rt, 0)
    assert_equal(len(res['stderr']), 0)
    assert(len(res['stdout']) > 0)
    assert_equal(res['merged'][0].split()[0], 'stdout')

@with_tempdir()
def test_minimal_test_run(wdir):
    lr = runner.LocalRunner(testbed_basedir=wdir)
    # pretty minimal test SPEC
    sp = '{"test":{"command":["uname"],"type":"shell_command"}}'
    sp_dict = spec.SPEC(sp)
    # gets version and id
    assert_true('id' in sp_dict)
    assert_equal(sp_dict['version'], 0)
    # run it
    retval, sp_out = lr(sp)
    # test passes
    assert_true(retval)
    # output is new dict
    assert_false(id(sp_dict) == id(sp_out))
    # embedded test ran fine
    tspec = sp_out['test']
    assert_equal(tspec['exitcode'], 0)
    assert_equal(tspec['stdout'].strip(), os.uname()[0])
    assert_true('stderr' in tspec)
    assert_true(os.path.exists(opj(lr.get_testbed_dir(sp_out), 'spec.json')))

@with_tempdir()
def test_failed_run(wdir):
    lr = runner.LocalRunner(testbed_basedir=wdir)
    # pretty minimal test SPEC
    sp = '{"test":{"command":["stupidddd111"],"type":"shell_command"}}'
    sp_dict = spec.SPEC(sp)
    # run it
    retval, sp_out = lr(sp)
    assert_false(retval == 0)
    # but should still come with system info
    assert_true('system' in sp_out)
    assert_true('stderr' in sp_out['test'])
