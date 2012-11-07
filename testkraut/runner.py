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
        get_script_interpreter, get_debian_pkgname, get_debian_pkginfo, \
        describe_system
from .spec import SPEC
from .base import verbose
if __debug__:
    from .base import debug


class BaseRunner(object):

    def __init__(self, testlib='library'):
        """
        Parameters
        ----------
        testlib: path
          Location of the test library.
        testbed_basedir: path
          Directory where local (non-VM, non-chroot) testbeds will be created.
        """
        self._testlib = os.path.abspath(testlib)

    def __call__(self, spec):
        testlib_filepath = opj(self._testlib, spec, 'spec.json')
        if os.path.isfile(testlib_filepath):
            # open spec from test library
            spec = SPEC(open(testlib_filepath))
        elif os.path.isfile(spec):
            # open explicit spec file
            spec = SPEC(open(spec))
        else:
            # spec is given as a str?
            spec = SPEC(spec)

        verbose(1, "processing test SPEC '%s' (%s)" % (spec['id'], spec.get_hash()))
        verbose(1, "check dependencies")
        verbose(1, "prepare testbed")
        self._prepare_testbed(spec)
        verbose(1, "run test")
        test_success = self._run_test(spec)
        if not test_success:
            return False, spec
        verbose(1, "gather component information")
        self._gather_component_info(spec)
        verbose(1, "fingerprinting results")
        self._fingerprint_output(spec)
        verbose(1, "evaluate test results")
        self._evaluate_output(spec)
        # store full SPEC into the testbed
        spec.save(opj(self.get_testbed_dir(spec), 'spec.json'))
        return True, spec

    def _prepare_testbed(self, spec):
        raise NotImplementedError

    def _run_test(self, spec):
        type_ = spec['test']['type']
        try:
            test_exec = getattr(self, '_run_%s' % type_)
        except AttributeError:
            raise ValueError("unsupported test type '%s'" % type_)
        if __debug__:
            debug('RUNNER', "run test via %s()" % test_exec.__name__)
        return test_exec(spec)

    def _check_output_presence(self, spec):
        raise NotImplementedError

    def _evaluate_output(self, spec):
        raise NotImplementedError

    def _fingerprint_output(self, spec):
        raise NotImplementedError

    def _gather_component_info(self, spec):
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
                if __debug__:
                    debug('RUNNER',
                          "hash for '%s' does not match ('%s' != '%s')"
                          % (filepath, observedhash, targethash))
                return False
            else:
                if __debug__:
                    debug('RUNNER',
                          "hash for '%s' matches ('%s')"
                          % (filepath, observedhash))
                return True
    if __debug__:
        debug('RUNNER', "no hash for '%s' found" % filepath)
    return None

def locate_file_in_testlib(testlibdir, testid, inspec=None, filename=None):
    if inspec is None:
        inspec = dict()
    if filename is None:
        filename = inspec['value']
    filepath = opj(testlibdir, testid, filename)
    if not os.path.isfile(filepath):
        if __debug__:
            debug('RUNNER', "file '%s' not present at '%s'"
                            % (filename, filepath))
        return None
    return filepath
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
        if __debug__:
            debug('RUNNER', "file '%s' not present in cache '%s'"
                            % (cand_filename, cachedir))
    return None

def prepare_local_testbed(spec, dst, testlibdir, cachedir=None, lazy=False):
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
            filepath = locate_file_in_testlib(testlibdir, spec['id'], inspec)
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
                if __debug__:
                    debug('RUNNER',
                          "skip copying already present file '%s'" % filepath)
        else:
            raise ValueError("unknown input spec type '%s'" % type_)
    # place test code/script itself
    testspec = spec['test']
    if 'file' in testspec:
        testfilepath = locate_file_in_testlib(testlibdir,
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

    def get_testbed_dir(self, spec):
        return opj(self._testbed_basedir, spec['id'])

    def _prepare_testbed(self, spec):
        prepare_local_testbed(spec,
                              opj(self._testbed_basedir, spec['id']),
                              self._testlib,
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
                if __debug__:
                    debug('RUNNER',
                          "local nipype version doesn't support provenance capture")
            return self._check_output_presence(spec)
        except RuntimeError, e:
            verbose(1, "%s: %s" % (e.__class__.__name__, str(e)))
            return False
        finally:
            os.chdir(initial_cwd)
        return False

    def _run_shell_command(self, spec):
        import subprocess
        testspec = spec['test']
        cmd = testspec['command']
        testbedpath = opj(self._testbed_basedir, spec['id'])
        # for the rest we need to execute stuff in the root of the testbed
        initial_cwd = os.getcwdu()
        os.chdir(testbedpath)
        try:
            texec = subprocess.Popen(cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            texec.wait()
            # record the exit code
            testspec['exitcode'] = texec.returncode
            # store test output
            for chan in ('stderr', 'stdout'):
                testspec[chan] = getattr(texec, chan).read()
            return self._check_output_presence(spec)
        except OSError, e:
            verbose(1, "%s: %s" % (e.__class__.__name__, str(e)))
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
        evalspecs = spec.get('evaluations',[])
        testbedpath = opj(self._testbed_basedir, spec['id'])
        initial_cwd = os.getcwdu()
        os.chdir(testbedpath)
        try:
            for espec in evalspecs:
                if __debug__:
                    debug('RUNNER', "running evaluation '%s'" % espec['id'])
                res = self._proc_eval_spec(espec, spec)
        finally:
            os.chdir(initial_cwd)


    def _proc_eval_spec(self, espec, spec):
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
            if __debug__:
                debug('RUNNER',
                      "generating fingerprints for '%s'" % filename)
            ospec['sha1sum'] = sha1sum(filename)
            # gather fingerprinting callables
            fingerprinters = set()
            for tag in ospec.get('tags', []):
                fingerprinters = fingerprinters.union(get_fingerprinters(tag))
            # store the fingerprint info in the SPEC of the respective output
            fingerprints = ospec.get('fingerprints', {}) 
            # for the unique set of fingerprinting functions
            for fingerprinter in fingerprinters:
                # their name will be used as the ID of the fingerprint
                finger_name = fingerprinter.__name__
                if finger_name.startswith('fp_'):
                    # strip common name prefix
                    finger_name = finger_name[3:]
                if __debug__:
                    debug('RUNNER',
                          "generating '%s' fingerprint" % finger_name)
                # run it, catch any error
                try:
                    fprint = {}
                    fingerprints[finger_name] = fprint
                    # fill in a dict to get whetever info even if an exception
                    # occurs during a latter stage of the fingerprinting
                    fingerprinter(filename, fprint)
                except Exception, e:
                    if __debug__:
                        debug('RUNNER',
                              "ignoring exception '%s' while fingerprinting '%s' with '%s'"
                              % (str(e), oname, finger_name))
            ospec['fingerprints'] = fingerprints
        os.chdir(initial_cwd)

    def _gather_component_info(self, spec):
        entities = {}
        spec['entities'] = entities
        spec['system'] = describe_system()
        # try using APT to obtain more info on software deps
        try:
            import apt
            pkg_mngr = apt.Cache()
        except:
            pkg_mngr = None
        for exec_path, espec in spec.get('executables', {}).iteritems():
            # replace exectutable info with the full picture
            ehash = self._describe_binary(exec_path,
                                          entities,
                                          type_='binary',
                                          pkgdb=pkg_mngr)
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
                    if __debug__:
                        debug('RUNNER',
                              "failed to read version from '%s'"
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
                        if __debug__:
                            debug('RUNNER',
                                  "failed to read version from '%s'" % vercmd)

        for env in spec.get('environment', {}):
            # grab envvar values
            spec['environment'][env] = os.environ.get(ename, 'UNDEFINED')
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
        provider = []
        # provided by debian?
        pkgname = get_debian_pkgname(fpath)
        if not pkgname is None:
            pkginfo = dict(type='debian_pkg', name=pkgname)
            pkginfo.update(get_debian_pkginfo(pkgname, pkgdb))
            if 'sha1sum' in pkginfo and len(pkginfo['sha1sum']):
                pkghash = pkginfo['sha1sum']
            else:
                pkghash = uuid().hex
            entities[pkghash] = pkginfo
            provider.append(pkghash)
        spec['provider'] = provider
        return fhash

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





class OldRunner(object):
    def __init__(self, spec):
        self.spec = spec
        self._log_fp = None

    def _raise(self, exception, why, input=None):
        if not input is None:
            input = ' (got: %s)' % repr(input)
        else:
            input = ''
        raise exception("RUNNER: %s%s" % (why, input))

    def _get_output_path(self, id):
        return opj('_output', id)

    def _log(self, msg, linebreak=True):
        fp = self._log_fp
        if fp is None:
            # assure existing output path
            outdir = self._get_output_path('')
            if not os.path.exists(outdir):
                os.mkdir(outdir)
            # open a logfile
            fp = self._log_fp = open(self._get_output_path('log'), 'w')
        # write msg
        fp.write(msg)
        # postproc
        if linebreak:
            fp.write('\n')

    def _proc_input_spec(self, specs):
        for spec_id in specs:
            spec = specs[spec_id]
            if not 'type' in spec:
                # we don't know what to do with it
                self._log("Ignore spec '%s' without type" % spec_id)
                continue
            # a big switch to handle all possible spec types
            spec_type = spec['type']
            self._log("Proc. spec '%s(%s)'" % (spec_id, spec_type))
            if spec_type == 'executable':
                path = None
                # check presence in current dir
                if os.path.isfile(spec_id):
                    statinfo = os.stat(spec_id)
                    # TODO check whether it is executable
                    path = spec_id
                else:
                    path = which(spec_id)
                if not path is None:
                    self._log("Found '%s(%s)' at '%s'"
                              % (spec_id, spec_type, path))
                else:
                    self._log("Cannot find '%s(%s)'" % (spec_id, spec_type))
                    return False

    def run(self):
        spec = self.spec
        # check the input
        # XXX check return value or rely on exceptions?
        self._log('Validate input specs')
        self._proc_input_spec(spec['inputs'])
        # run the actual test command
        command = spec['command']
        ret = None
        if not command is None:
            self._log("Run test command [%s]" % command)
            ret = run_command(command)
        # handle test output
        self._proc_output_spec(spec['outputs'], ret)
        # pass the return value of the test command, or pretend all is good
        # if no command was given
        if ret is None:
            return 0
        else:
            return ret['retval']

    def _write_line_to_file(self, filename, lines):
        out_fp = open(filename, 'w')
        for line in lines:
            out_fp.write(line)
            out_fp.write('\n')

    def _proc_output_spec(self, specs, ret):
        if not ret is None:
            # if an actual test command was executed
            open(self._get_output_path('retval'), 'w').write(
                    '%i\n' % ret['retval'])
            self._write_line_to_file(self._get_output_path('stdout'),
                                     ret['stdout'])
            self._write_line_to_file(self._get_output_path('stderr'),
                                     ret['stderr'])
            self._log('=== Test output between markers ======================')
            self._log('\n'.join(ret['merged']))
            self._log('======================================================')

        self._log('Process output specs')
        # loop over all output specs and see what we can handle
        for spec_id in specs:
            spec = specs[spec_id]
            spec_path = self._get_output_path(spec_id)
            if not 'type' in spec:
                # we don't know what to do with it
                self._log("Ignore spec '%s' without type" % spec_id)
                continue
            # a big switch to handle all possible spec types
            spec_type = spec['type']
            self._log("Proc. spec '%s(%s)'" % (spec_id, spec_type))
            if spec_type == 'shlibdeps':
                self._write_line_to_file(spec_path,
                                         get_shlibdeps(which(spec['binary'])))
            elif spec_type == 'file':
                spec_source = os.path.expandvars(spec['source'])
                if not os.path.isfile(spec_source):
                    if 'optional' in spec and spec['optional'] == 'yes':
                        # just skip if file is not there and optional
                        continue
                done = False
                if hasattr(os, 'link'):
                    if os.path.exists(spec_path):
                        os.unlink(spec_path)
                    try:
                        os.link(spec_source, spec_path)
                        done = True
                    except OSError:
                        # silently fail if linking doesn't work (e.g.
                        # cross-device link ... will recover later
                        pass
                if not done:
                    shutil.copy(spec_source, spec_path)

