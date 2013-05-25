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
import re
import shutil
from datetime import datetime
from uuid import uuid1 as uuid
from . import utils
from . import evaluators
from .utils import run_command, get_shlibdeps, which, sha1sum, \
        get_script_interpreter, describe_system, get_test_library_paths
from .pkg_mngr import PkgManager
from .spec import SPEC
import testkraut
from testkraut import cfg
import logging
lgr = logging.getLogger(__name__)

#class LocalRunner(BaseRunner):
#    def __init__(self, testbed_basedir='testbeds', cachedir=None, **kwargs):
#        """
#        Parameters
#        ----------
#        testbed_basedir: path
#          Directory where local (non-VM, non-chroot) testbeds will be created.
#        """
#        BaseRunner.__init__(self, **kwargs)
#        self._testbed_basedir = os.path.abspath(testbed_basedir)
#        self._cachedir = cachedir
#        if cachedir is None:
#            self._cachedir = utils.get_filecache_dir()
#        self._pkg_mngr = PkgManager()
#
#    def _evaluate_output(self, spec):
#        evalspecs = spec.get('comparisons',{})
#        testbedpath = opj(self._testbed_basedir, spec['id'])
#        initial_cwd = os.getcwdu()
#        os.chdir(testbedpath)
#        try:
#            for eid, espec in evalspecs.iteritems():
#                lgr.debug("running comparison '%s'" % espec['id'])
#                res = self._proc_eval_spec(eid, espec, spec)
#        finally:
#            os.chdir(initial_cwd)
#
#    def _proc_eval_spec(self, eid, espec, spec):
#        op_spec = espec['operator']
#        op_type = op_spec['type']
#        if op_type in ('builtin-func', 'builtin-class'):
#            operator = getattr(evaluators, op_spec['name'])
#        else:
#            raise NotImplementedError(
#                    "dunno how to deal with operator type '%s'" % op_type)
#        # gather inputs
#        args = list()
#        kwargs = dict()
#        in_spec = espec['inputs']
#        for ins in in_spec:
#            # This distinction is bullshit and not possible with valid JSON
#            if isinstance(ins, basestring):
#                # kwarg
#                raise NotImplementedError('dunno how to handle kwargs in comparison input specs')
#            else:
#                # arg
#                args.append(get_eval_input(ins, spec))
#        return operator(*args, **kwargs)
#
def get_eval_input(inspec, testspec):
    if 'origin' in inspec and inspec['origin'] == 'testoutput':
        # reference to a test output
        outspec = testspec['outputs'][inspec['value']]
        if outspec['type'] == 'file':
            return outspec['value']
        else:
            raise NotImplementedError(
                "dunno how to handle references to non-file test output of '%s'"
                % inspec['value'])
    else:
        raise NotImplementedError("dunno how to handle anything but output references")
