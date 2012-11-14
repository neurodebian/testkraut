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

class BaseRunner(object):
    """Execute a test SPEC.

    A runner instance is called with a SPEC object. The runner uses the SPEC to
    check the requirements of the test, execute the test, and finally evaluate
    the test outputs and gather information on the computational environment.
    All collected information is added to the input SPEC object. Even in the
    event of a test failure the input SPEC will contain all information
    collected up to the point of failure.
    """
    def __init__(self, testlibs=None):
        """
        Parameters
        ----------
        testlibs: list
          sequence of test library locations. The paths are prepended to the
          configured test library locations (defined via a config file).
        testbed_basedir: path
          Directory where local (non-VM, non-chroot) testbeds will be created.
        """
        self._testlibdirs = [os.path.abspath(os.path.expandvars(tld))
                                    for tld in get_test_library_paths(testlibs)]
        lgr.debug("effective test library paths: '%s'" % self._testlibdirs)

    def __call__(self, spec):
        lgr.info("processing test SPEC '%s' (%s)" % (spec['id'], spec.get_hash()))
        lgr.info("check requirements")
        self._check_requirements(spec)
        lgr.info("prepare testbed")
        self._prepare_testbed(spec)
        lgr.info("run test")
        test_success = self._run_test(spec)
        if not test_success:
            return False
        lgr.info("gather component information")
        self._gather_component_info(spec)
        lgr.info("fingerprinting results")
        self._fingerprint_output(spec)
        lgr.info("evaluate test results")
        self._evaluate_output(spec)
        return True

    def _prepare_testbed(self, spec):
        raise NotImplementedError

    def _run_test(self, spec):
        type_ = spec['test']['type']
        try:
            test_exec = getattr(self, '_run_%s' % type_)
        except AttributeError:
            raise ValueError("unsupported test type '%s'" % type_)
        lgr.debug("run test via %s()" % test_exec.__name__)
        return test_exec(spec)

    def _check_output_presence(self, spec):
        raise NotImplementedError

    def _evaluate_output(self, spec):
        raise NotImplementedError

    def _fingerprint_output(self, spec):
        raise NotImplementedError

    def _gather_component_info(self, spec):
        raise NotImplementedError

    def _check_requirements(self, spec):
        raise NotImplementedError

    def get_testbed_dir(self, spec):
        raise NotImplementedError


def check_file_hash(filepath, inspec):
    # hash match check
    for hashtype in ('md5sum', 'sha1sum'):
        if hashtype in inspec:
            targethash = inspec[hashtype]
            hasher = getattr(utils, hashtype)
            observedhash = hasher(filepath)
            if targethash != observedhash:
                lgr.debug("hash for '%s' does not match ('%s' != '%s')"
                          % (filepath, observedhash, targethash))
                return False
            else:
                lgr.debug("hash for '%s' matches ('%s')"
                          % (filepath, observedhash))
                return True
    lgr.debug("no hash for '%s' found" % filepath)
    return None

def _locate_file_in_testlib(testlibdirs, testid, inspec=None, filename=None):
    if inspec is None:
        inspec = dict()
    if filename is None:
        filename = inspec['value']
    for tld in testlibdirs:
        filepath = opj(tld, testid, filename)
        if os.path.isfile(filepath):
            return filepath
        lgr.debug("file '%s' not present at '%s'" % (filename, filepath))
    return None

def locate_file_in_cache(cachedir, inspec):
    if inspec is None:
        inspec = dict()
    if not 'sha1sum' in inspec:
        # nothing we can do
        return None
    cand_filename = opj(cachedir, inspec['sha1sum'])
    if os.path.isfile(cand_filename):
        return cand_filename
    else:
        lgr.debug("file '%s' not present in cache '%s'"
                  % (cand_filename, cachedir))
    return None

def prepare_local_testbed(spec, dst, testlibdirs, cachedir=None, lazy=False):
    if not os.path.exists(dst):
        os.makedirs(dst)
    inspecs = spec.get('inputs', {})
    # locate and copy test input into testbed
    for inspec_id in inspecs:
        inspec = inspecs[inspec_id]
        type_ = inspec['type']
        if type_ == 'file':
            # try finding the file locally
            testbed_filepath = inspec['value']
            filepath = _locate_file_in_testlib(testlibdirs, spec['id'], inspec)
            if filepath is None and os.path.isfile(testbed_filepath):
                # that file actually exists in the current dir
                filepath = testbed_filepath
            if filepath is None and not cachedir is None:
                # check the cache
                filepath = locate_file_in_cache(cachedir, inspec)
            if filepath is None:
                raise NotImplementedError("come up with more ideas on locating files")
            if not check_file_hash(filepath, inspec) in (True, None):
                # if there is no hash we need to trust
                raise ValueError("input file at '%s' doesn match checksum"
                                 % filepath)
            dst_path = opj(dst, testbed_filepath)
            if not os.path.isfile(dst_path) or not lazy:
                target_dir = os.path.dirname(dst_path)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                shutil.copy(filepath, dst_path)
            else:
                lgr.debug("skip copying already present file '%s'" % filepath)
        else:
            raise ValueError("unknown input spec type '%s'" % type_)
    # place test code/script itself
    testspec = spec['test']
    if 'file' in testspec:
        testfilepath = _locate_file_in_testlib(testlibdirs,
                                              spec['id'],
                                              filename=testspec['file'])
        if testfilepath is None:
            raise ValueError("file '%s' referenced in test '%s' not found"
                             % (testspec['file'], spec['id']))
        shutil.copy(testfilepath, dst)
    elif 'command' in testspec:
        # nothing to move
        pass
    else:
        raise NotImplementedError("can't deal with anything but test scripts for now")



#class ChrootRunner
#class VMRunner
class LocalRunner(BaseRunner):
    def __init__(self, testbed_basedir='testbeds', cachedir='filecache', **kwargs):
        """
        Parameters
        ----------
        testbed_basedir: path
          Directory where local (non-VM, non-chroot) testbeds will be created.
        """
        BaseRunner.__init__(self, **kwargs)
        self._testbed_basedir = os.path.abspath(testbed_basedir)
        self._cachedir = cachedir
        self._pkg_mngr = PkgManager()

    def get_testbed_dir(self, spec):
        return opj(self._testbed_basedir, spec['id'])

    def _prepare_testbed(self, spec):
        prepare_local_testbed(spec,
                              opj(self._testbed_basedir, spec['id']),
                              self._testlibdirs,
                              cachedir=self._cachedir)

    def _run_nipype_workflow(self, spec):
        testspec = spec['test']
        testbedpath = opj(self._testbed_basedir, spec['id'])
        if 'file' in testspec:
            testwffilepath = testspec['file']
        else:
            testwffilepath = 'workflow.py'
        testwffilepath = opj(testbedpath, testwffilepath)
        # for the rest we need to execute stuff in the root of the testbed
        initial_cwd = os.getcwdu()
        os.chdir(testbedpath)
        # execute the script and extract the workflow
        locals = dict()
        try:
            execfile(testwffilepath, dict(), locals)
        except Exception, e:
            raise e.__class__(
                    "exception while executing workflow setup script (%s): %s"
                    % (testwffilepath, str(e)))
        if not len(locals) or not 'test_workflow' in locals:
            raise RuntimeError("test workflow script '%s' did not create a 'test_workflow' object"
                               % testwffilepath)
        workflow = locals['test_workflow']
        # make sure nipype executes it in the right place
        workflow.base_dir=os.path.abspath(opj(testbedpath, '_workflow_exec'))
        # we want content, not time based hashing
        if 'execution' in workflow.config:
            workflow.config['execution']['hash_method'] = "content"
        else:
            workflow.config['execution'] = dict(hash_method="content")
        try:
            exec_graph = workflow.run()
            # try dumping provenance info
            try:
                from nipype.pipeline.utils import write_prov
                write_prov(exec_graph,
                           filename=opj(workflow.base_dir, 'provenance.json'))
            except ImportError:
                lgr.debug("local nipype version doesn't support provenance capture")
            return self._check_output_presence(spec)
        except RuntimeError, e:
            lgr.info("%s: %s" % (e.__class__.__name__, str(e)))
            return False
        finally:
            os.chdir(initial_cwd)
        return False

    def _run_shell_command(self, spec):
        import subprocess
        testspec = spec['test']
        cmd = testspec['command']
        if isinstance(cmd, list):
            # convert into a cmd string to execute via shell
            # to get all envvar expansion ...
            cmd = subprocess.list2cmdline(cmd)
        testbedpath = opj(self._testbed_basedir, spec['id'])
        # for the rest we need to execute stuff in the root of the testbed
        initial_cwd = os.getcwdu()
        os.chdir(testbedpath)
        try:
            lgr.debug("attempting to execute command '%s'" % cmd)
            texec = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
            texec.wait()
            # record the exit code
            testspec['exitcode'] = texec.returncode
            # store test output
            for chan in ('stderr', 'stdout'):
                testspec[chan] = getattr(texec, chan).read()
                lgr.debug('%s: %s' % (chan, testspec[chan]))
            return self._check_output_presence(spec)
        except OSError, e:
            lgr.error("%s: %s" % (e.__class__.__name__, str(e)))
            return False
        finally:
            os.chdir(initial_cwd)
        return False

    def _check_output_presence(self, spec):
        testbedpath = opj(self._testbed_basedir, spec['id'])
        outspec = spec.get('outputs', {})
        missing = []
        for ospec_id in outspec:
            ospec = outspec[ospec_id]
            if not ospec['type'] == 'file':
                raise NotImplementedError("dunno how to handle non-file output yet")
            if not os.path.isfile(ospec['value']):
                missing.append(ospec_id)
            # TODO check for file type
        if len(missing):
            raise RuntimeError("expected output(s) %s not found" % missing)
        return True

    def _evaluate_output(self, spec):
        evalspecs = spec.get('evaluations',{})
        testbedpath = opj(self._testbed_basedir, spec['id'])
        initial_cwd = os.getcwdu()
        os.chdir(testbedpath)
        try:
            for eid, espec in evalspecs.iteritems():
                lgr.debug("running evaluation '%s'" % espec['id'])
                res = self._proc_eval_spec(eid, espec, spec)
        finally:
            os.chdir(initial_cwd)


    def _proc_eval_spec(self, eid, espec, spec):
        op_spec = espec['operator']
        op_type = op_spec['type']
        if op_type in ('builtin-func', 'builtin-class'):
            operator = getattr(evaluators, op_spec['name'])
        else:
            raise NotImplementedError(
                    "dunno how to deal with operator type '%s'" % op_type)
        # gather inputs
        args = list()
        kwargs = dict()
        in_spec = espec['inputs']
        for ins in in_spec:
            # This distinction is bullshit and not possible with valid JSON
            if isinstance(ins, basestring):
                # kwarg
                raise NotImplementedError('dunno how to handle kwargs in eval input specs')
            else:
                # arg
                args.append(get_eval_input(ins, spec))
        return operator(*args, **kwargs)

    def _fingerprint_output(self, spec):
        from .fingerprinting import get_fingerprinters
        from .utils import sha1sum
        # all local to the testbed
        testbedpath = opj(self._testbed_basedir, spec['id'])
        initial_cwd = os.getcwdu()
        os.chdir(testbedpath)
        # for all known outputs
        for oname, ospec in spec.get_outputs('file').iteritems():
            filename = ospec['value']
            lgr.debug("generating fingerprints for '%s'" % filename)
            ospec['sha1sum'] = sha1sum(filename)
            # gather fingerprinting callables
            fingerprinters = set()
            for tag in ospec.get('tags', []):
                fingerprinters = fingerprinters.union(get_fingerprinters(tag))
            # store the fingerprint info in the SPEC of the respective output
            fingerprints = ospec.get('fingerprints', {}) 
            # for the unique set of fingerprinting functions
            for fingerprinter in fingerprinters:
                _proc_fingerprint(fingerprinter, fingerprints, filename)
            ospec['fingerprints'] = fingerprints
        os.chdir(initial_cwd)

    def _gather_component_info(self, spec):
        entities = {}
        spec['entities'] = entities
        spec['system'] = describe_system()
        for exec_path, espec in spec.get('executables', {}).iteritems():
            # replace exectutable info with the full picture
            ehash = self._describe_binary(exec_path,
                                          entities,
                                          type_='binary')
            # link the old info with the new one
            espec['entity'] = ehash
            # check version information
            have_version = False
            if 'version_file' in espec:
                verfilename = espec['version_file']
                extract_regex = r'.*'
                if isinstance(verfilename, list):
                    verfilename, extract_regex = verfilename
                # expand the filename
                verfilename = os.path.realpath(os.path.expandvars(verfilename))
                try:
                    file_content = open(verfilename).read().strip()
                    version = re.findall(extract_regex, file_content)[0]
                    if len(version):
                        entities[ehash]['version'] = version
                        have_version = True
                except:
                    lgr.debug("failed to read version from '%s'"
                              % verfilename)
            if not have_version and 'version_cmd' in espec:
                vercmd = espec['version_cmd']
                extract_regex = r'.*'
                if isinstance(vercmd, list):
                    vercmd, extract_regex = vercmd
                ret = run_command(vercmd)
                try:
                    # this will throw an exception if nothing is found
                    version = re.findall(extract_regex, '\n'.join(ret['stderr']))[0]
                    if len(version):
                        entities[ehash]['version'] = version
                        have_version = True
                except:
                    try:
                        version = re.findall(extract_regex, '\n'.join(ret['stdout']))[0]
                        if len(version):
                            entities[ehash]['version'] = version
                            have_version = True
                    except:
                        lgr.debug("failed to read version from '%s'" % vercmd)

        for env in spec.get('environment', {}):
            # grab envvar values
            spec['environment'][env] = os.environ.get(env, 'UNDEFINED')
        if not len(entities):
            # remove unnecessary dict
            del spec['entities']


    def _describe_binary(self, path, entities, type_=None, pkgdb=None):
        spec = dict(path=path)
        fpath = os.path.realpath(os.path.expandvars(path))
        spec['realpath'] = fpath
        fhash = sha1sum(fpath)
        spec['sha1sum'] = fhash
        if fhash in entities:
            # do not process twice
            return fhash
        else:
            entities[fhash] = spec
        if not type_ is None:
            spec['type'] = type_
        # try capturing dependencies
        try:
            shlibdeps = get_shlibdeps(fpath)
            if len(shlibdeps):
                spec['shlibdeps'] = []
        except RuntimeError:
            shlibdeps = list()
        # maybe not a binary, but could be a script
        try:
            interpreter_path = get_script_interpreter(fpath)
            spec['type'] = 'script'
            spec['interpreter'] = self._describe_binary(interpreter_path,
                                                        entities,
                                                        pkgdb=pkgdb)
        except ValueError:
            # not sure what this was
            pass
        for dep in shlibdeps:
            spec['shlibdeps'].append(self._describe_binary(dep, entities,
                                                           type_='library',
                                                           pkgdb=pkgdb))
        # provided by a package?
        pkgname = self._pkg_mngr.get_pkg_name(fpath)
        if not pkgname is None:
            pkg_pltf = self._pkg_mngr.get_platform_name()
            pkginfo = dict(type=pkg_pltf, name=pkgname)
            pkginfo.update(self._pkg_mngr.get_pkg_info(pkgname))
            if 'sha1sum' in pkginfo and len(pkginfo['sha1sum']):
                pkghash = pkginfo['sha1sum']
            else:
                pkghash = uuid().hex
            entities[pkghash] = pkginfo
            spec['provider'] = pkghash
        return fhash

    def _check_requirements(self, spec):
        for env in spec.get('environment', {}):
            if not env in os.environ:
                raise ValueError("required environment variable '%s' not set"
                                 % env)

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

def _proc_fingerprint(fingerprinter, fingerprints, filename):
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
        fingerprinter(filename, fprint)
    except Exception, e:
        lgr.debug("ignoring exception '%s' while fingerprinting '%s' with '%s'"
                  % (str(e), filename, finger_name))
