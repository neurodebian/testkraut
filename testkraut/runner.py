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
#    def _fingerprint_output(self, spec):
#        from .fingerprints import get_fingerprinters
#        from .utils import sha1sum
#        # all local to the testbed
#        testbedpath = opj(self._testbed_basedir, spec['id'])
#        initial_cwd = os.getcwdu()
#        os.chdir(testbedpath)
#        # for all known outputs
#        ofilespecs = spec.get_outputs('file')
#        # cache fingerprinted files tp avoid duplication for identical files
#        fp_cache = {}
#        # deterministic order to help stabilize reference filename for duplicates
#        for oname in sorted(ofilespecs.keys()):
#            ospec = ofilespecs[oname]
#            filename = ospec['value']
#            sha1 = sha1sum(filename)
#            ospec['sha1sum'] = sha1
#            if sha1 in fp_cache:
#                ospec['identical_with'] = fp_cache[sha1]
#                lgr.debug("'%s' is a duplicate of '%s'" % (oname, fp_cache[sha1]))
#                continue
#            lgr.debug("generating fingerprints for '%s'" % filename)
#            # gather fingerprinting callables
#            fingerprinters = set()
#            for tag in ospec.get('tags', []):
#                fingerprinters = fingerprinters.union(get_fingerprinters(tag))
#            # store the fingerprint info in the SPEC of the respective output
#            fingerprints = ospec.get('fingerprints', {}) 
#            # for the unique set of fingerprinting functions
#            for fingerprinter in fingerprinters:
#                _proc_fingerprint(fingerprinter, fingerprints, filename,
#                                  ospec.get('tags', []))
#            ospec['fingerprints'] = fingerprints
#        os.chdir(initial_cwd)
#
#    def _check_requirements(self, spec):
#        for env in spec.get('environment', {}):
#            if not env in os.environ:
#                raise ValueError("required environment variable '%s' not set"
#                                 % env)
#        exes = spec.get('executables', {})
#        for exe in exes:
#            optional = exes[exe].get('optional', False)
#            if not optional and not os.path.isfile(os.path.expandvars(exe)):
#                raise ValueError("required executable '%s' not found" % exe)
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

def _proc_fingerprint(fingerprinter, fingerprints, filename, tags=None):
    if tags is None:
        tags = []
    finger_name = fingerprinter.__name__
    if finger_name.startswith('fp_'):
        # strip common name prefix
        finger_name = finger_name[3:]
    lgr.debug("generating '%s' fingerprint" % finger_name)
    # run it, catch any error
    try:
        fprint = {}
        fingerprints[finger_name] = fprint
        # fill in a dict to get whetever info even if an exception
        # occurs during a latter stage of the fingerprinting
        fingerprinter(filename, fprint, tags)
    except Exception, e:
        fprint['__exception__'] = '%s: %s' % (type(e), e.message)
        # XXX maybe better a warning?
        lgr.debug("ignoring exception '%s' while fingerprinting '%s' with '%s'"
                  % (str(e), filename, finger_name))
