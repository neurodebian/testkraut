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
import re
import subprocess
import select
import datetime
import hashlib
import platform
from .pkg_mngr import PkgManager
import testkraut
from os.path import join as opj
from .spec import SPEC
import logging
lgr = logging.getLogger(__name__)

def which(program):
    """
    http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    """
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    def ext_candidates(fpath):
        yield fpath
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            yield fpath + ext

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            for candidate in ext_candidates(exe_file):
                if is_exe(candidate):
                    return candidate

    return None


class Stream(object):
    # this has been taken from Nipype (BSD-3-clause license)
    """Function to capture stdout and stderr streams with timestamps

    http://stackoverflow.com/questions/4984549/merge-and-sync-stdout-and-stderr/5188359#5188359
    """

    def __init__(self, name, impl):
        self._name = name
        self._impl = impl
        self._buf = ''
        self._rows = []
        self._lastidx = 0

    def fileno(self):
        "Pass-through for file descriptor."
        return self._impl.fileno()

    def read(self, drain=0):
        "Read from the file descriptor. If 'drain' set, read until EOF."
        while self._read(drain) is not None:
            if not drain:
                break

    def _read(self, drain):
        "Read from the file descriptor"
        fd = self.fileno()
        buf = os.read(fd, 4096)
        if not buf and not self._buf:
            return None
        if '\n' not in buf:
            if not drain:
                self._buf += buf
                return []

        # prepend any data previously read, then split into lines and format
        buf = self._buf + buf
        if '\n' in buf:
            tmp, rest = buf.rsplit('\n', 1)
        else:
            tmp = buf
            rest = None
        self._buf = rest
        now = datetime.datetime.now().isoformat()
        rows = tmp.split('\n')
        self._rows += [(now, '%s %s:%s' % (self._name, now, r), r) for r in rows]
        self._lastidx = len(self._rows)



def run_command(cmdline, cwd=None, env=None, timeout=0.01):
    # this has been taken from Nipype (BSD-3-clause license)
    """
    Run a command, read stdout and stderr, prefix with timestamp. The returned
    runtime contains a merged stdout+stderr log with timestamps

    http://stackoverflow.com/questions/4984549/merge-and-sync-stdout-and-stderr/5188359#5188359
    """
    PIPE = subprocess.PIPE
    proc = subprocess.Popen(cmdline,
                            stdout=PIPE,
                            stderr=PIPE,
                            shell=True,
                            cwd=cwd,
                            env=env)
    streams = [
        Stream('stdout', proc.stdout),
        Stream('stderr', proc.stderr)
        ]

    def _process(drain=0):
        try:
            res = select.select(streams, [], [], timeout)
        except select.error, e:
            if e[0] == errno.EINTR:
                return
            else:
                raise
        else:
            for stream in res[0]:
                stream.read(drain)

    while proc.returncode is None:
        proc.poll()
        _process()
    returncode = proc.returncode
    _process(drain=1)

    # collect results, merge and return
    result = {}
    temp = []
    for stream in streams:
        rows = stream._rows
        temp += rows
        result[stream._name] = [r[2] for r in rows]
    temp.sort()
    result['merged'] = [r[1] for r in temp]
    result['retval'] = returncode
    return result

def get_shlibdeps(binary):
    # for now only unix
    cmd = 'ldd %s' % binary
    ret = run_command(cmd)
    if not ret['retval'] == 0:
        raise RuntimeError("An error occurred while executing '%s'\n%s"
                           % (cmd, '\n'.join(ret['stderr'])))
    else:
        deps = [re.match(r'.*=> (.*) \(.*', l) for l in ret['stdout']]
        return [d.group(1) for d in deps if not d is None and len(d.group(1))]

def get_script_interpreter(filename):
    shebang = open(filename).readline()
    match = re.match(r'^#!(.*)$', shebang)
    if match is None:
        raise ValueError("no valid shebang line found in '%s'" % filename)
    return match.group(1).strip()

def hash(filename, method):
    hash = method
    with open(filename,'rb') as f: 
        for chunk in iter(lambda: f.read(128*hash.block_size), b''): 
             hash.update(chunk)
    return hash.hexdigest()

def sha1sum(filename):
    return hash(filename, hashlib.sha1())

def md5sum(filename):
    return hash(filename, hashlib.md5())

def _get_next_pid_id(procs, pid):
    base_pid = pid
    pid_suffix = 0
    while pid in procs:
        pid = '%s.%i' % (base_pid, pid_suffix)
        pid_suffix += 1
    return pid

def _find_parent_with_argv(procs, proc, match_argv):
    if proc['started_by'] is None:
        # reached the top
        return proc['pid']
    parent_proc = procs[proc['started_by']]
    if not parent_proc['argv'] is None \
       and not match_argv.match(parent_proc['argv'][0]) is None:
        return parent_proc['pid']
    else:
        return _find_parent_with_argv(procs, parent_proc, match_argv)

def _get_new_proc(procs, pid):
    oldpid = None
    if pid in procs:
        # archive a potentially existing proc of this PID under a safe
        # new PID
        oldpid = _get_next_pid_id(procs, pid)
        proc = procs[pid]
        proc['pid'] = oldpid
        procs[oldpid] = proc
    proc = dict(dict(pid=pid, started_by=None, argv=None,
                     uses=[], generates=[]))
    procs[pid] = proc
    return proc, oldpid

def get_cmd_prov_strace(cmd, match_argv=None):
    if match_argv is None:
        match_argv = r'.*'
    match_argv = re.compile(match_argv)
    cmd_prefix = ['strace', '-q', '-f', '-s', '1024',
                  '-e', 'trace=execve,clone,open,openat,unlink,unlinkat']
    cmd = cmd_prefix + cmd
    cmd_exec = subprocess.Popen(cmd, bufsize=0,
                             stderr=subprocess.PIPE)
    # store discovered processes
    procs = {}
    # store accessed files
    files = {}
    curr_proc = None
    # precompile REs
    quoted_list_splitter = re.compile(r'(?:[^,"]|"[^"]*\")+')
    syscall_arg_splitter = re.compile(r'(?:[^,[]|\[[^]]*\])+')
    #strace_ouput_splitter = re.compile(r'^(\[pid\s+([0-9]+)\] |)([a-z0-9_]+)\((.*)\) (.*)')
    strace_output_splitter = re.compile(r'^(\[pid\s+([0-9]+)\] |)([a-z0-9_]+)\((.*)')
    strace_resume_splitter = re.compile(r'^(\[pid\s+([0-9]+)\] |)<\.\.\. ([a-z0-9_]+) resumed> (.*)')
    unfinished_splitter = re.compile(r'(.*)\s+<unfinished \.\.\.>')
    rest_splitter = re.compile(r'(.*)\s+=\s+(.*)')
    # for every line in strace's output
    root_pid = None
    unfinished = {}
    for line in cmd_exec.stderr:
        match = strace_output_splitter.match(line)
        if match is None:
            # this could be a resume line
            match = strace_resume_splitter.match(line)
            if match is None:
                # ignore funny line
                continue
            # we have a resume, check if we know the beginning of it
            _, pid, syscall, rest = match.groups()
            if pid in unfinished:
                pdict = unfinished[pid]
                if syscall in pdict:
                    start = pdict[syscall]
                    del pdict[syscall]
                else:
                    raise RuntimeError("no resume info on started syscall (%s, %s)"
                                       % (syscall, pid))
                if not len(pdict):
                    del unfinished[pid]
            else:
                raise RuntimeError("no resume info on pid %s"
                                   % pid)
            rest = '%s %s' % (start, rest)
        else:
            #_, pid, syscall, syscall_args, syscall_ret = match.groups()
            _, pid, syscall, rest = match.groups()
            umatch = unfinished_splitter.match(rest)
            if not umatch is None:
                # this is the start of an unfinished syscall
                pdict = unfinished.get(pid, dict())
                pdict[syscall] = umatch.group(1)
                unfinished[pid] = pdict
                continue # will be processed on resume
        syscall_args, syscall_ret = rest_splitter.match(rest).groups()
        if not pid is None and not pid == root_pid and not pid in procs:
            if not root_pid is None:
                raise RuntimeError("we already have a root PID, and found a new one")
            root_pid = pid
        if pid is None:
            pid = 'mother'
        if syscall_ret.startswith('-'):
            # ignore any syscall that yielded an error
            continue
        # everything we know about this process
        if not pid in procs:
            proc, _ = _get_new_proc(procs, pid)
        else:
            proc = procs[pid]
        # split the syscall args into a list
        syscall_args = syscall_arg_splitter.findall(syscall_args)
        if syscall == 'clone':
            newpid = syscall_ret
            # it started a new proc
            new_proc, _ = _get_new_proc(procs, newpid)
            new_proc['started_by'] = pid
        elif syscall == 'execve':
            # start a process
            executable = syscall_args[0].strip('"')
            argv = [arg.strip(' "') for arg in
                        quoted_list_splitter.findall(syscall_args[1].strip(' []'))]
            if not proc['argv'] is None:
                # a new command in the same process -> code as a new process)
                new_proc, oldpid = _get_new_proc(procs, pid)
                new_proc['started_by'] = oldpid
                proc = new_proc
            proc.update(dict(executable=executable,
                             argv=argv))
        elif syscall == 'open':
            # open a file
            open_args = [arg.strip(' "') for arg in syscall_args]
            filename = os.path.relpath(open_args[0])
            access_mode = open_args[1]
            if filename.startswith(os.path.pardir):
                # track files under the current dir only
                continue
            if 'O_WRONLY' in access_mode or 'O_RDWR' in access_mode:
                proc['generates'].append(filename)
            elif 'O_RDONLY' in access_mode or 'O_RDWR' in access_mode:
                proc['uses'].append(filename)
        else:
            # ignore all other syscalls
            pass
    # rewrite PID of the root process if we got to know it
    if not root_pid is None:
        # merge the info of root_pid with the mother's
        rproc = procs[root_pid]
        for pid, proc in procs.iteritems():
            if pid.startswith('mother'):
                for attr in ('generates', 'uses'):
                    proc[attr] += rproc[attr]
                    proc[attr] = [a.replace('mother', root_pid)
                                    for a in proc[attr]]
                proc['pid'] = pid.replace('mother', root_pid)
            for attr in ('started_by',):
                if not proc[attr] is None:
                    proc[attr] = proc[attr].replace('mother', root_pid)
            #REPLACE ALL MOTHER REFERENCES IN ALL ATTRS
        del procs[root_pid]
        procs = dict([(pid.replace('mother', root_pid), info) for pid, info in procs.iteritems()])
    # uniquify
    for pid, proc in procs.iteritems():
        for attr in ('generates', 'uses'):
            proc[attr] = set(proc[attr])
    # rewrite inter-proc dependencies to point to processes with cmdinfo
    pid_mapper = {}
    for pid, proc in procs.iteritems():
        if proc['started_by'] is None:
            # cache pid of the mother
            if 'argv' in proc:
                pid_mapper[pid] = pid
            # nothing else to recode
            continue
        # we have a parent process, but we might have no cmd info
        # -> retrace graph upwards to find a parent with info
        parent_pid = proc['started_by']
        new_parent_pid = pid_mapper.get(parent_pid,
                                        _find_parent_with_argv(procs,
                                                               proc,
                                                               match_argv))
        # cache pid mapping: old parent -> new parent
        # (even if it woudl be the same)
        pid_mapper[parent_pid] = new_parent_pid
        # rewrite parent in current process
        proc['started_by'] = new_parent_pid
        if proc['argv'] is None \
           or match_argv.match(['argv'][0]) is None:
            # we don't want to know about this process
            # move the files it uses and generates upwards
            new_parent_proc = procs[new_parent_pid]
            for field in ('uses', 'generates'):
                new_parent_proc[field] = new_parent_proc[field].union(proc[field])
        else:
            # this proc info stays
            pid_mapper[pid] = pid
    # filter all procs that have no argv
    procs = dict([(pid, procs[pid]) for pid in pid_mapper.values()])
    # wait() sets the returncode
    cmd_exec.wait()
    return procs, cmd_exec.returncode

def guess_file_tags(fname):
    tags = set()
    if not os.path.getsize(fname):
        # no futher tags for empty files
        tags.add('empty')
        return tags
    try:
        import nibabel as nb
        img = nb.load(fname)
        tags.add('volumetric image')
        tags.add('%iD image' % len(img.get_shape()))
    except:
        pass
    try:
        import numpy as np
        mat = np.loadtxt(fname)
        tags.add('space-separated values')
        tags.add('text file')
    except:
        pass
    return tags

def describe_system():
    sysinfo = {}
    for fx in ('architecture', 'machine', 'python_build', 'python_compiler',
               'python_branch', 'python_implementation', 'python_revision',
               'python_version', 'release', 'system'):
        if hasattr(platform, fx):
            sysinfo[fx] = getattr(platform, fx)()
    # core deps
    for pkg in ('numpy', 'scipy', 'nibabel'):
        try:
            imp_pkg = __import__(pkg, globals(), locals(), [], -1)
            sysinfo['pkg_%s_version' % pkg] = imp_pkg.__version__
        except (ImportError, AttributeError):
            sysinfo['pkg_%s_version' % pkg] = None
    # trigger platform hooks
    if len(sysinfo.get('system', '')):
        system_descr = '_describe_%s_system' % sysinfo['system'].lower()
        if system_descr in globals():
            globals()[system_descr](sysinfo)
    return sysinfo

def _describe_linux_system(sysinfo):
    for fx in ('linux_distribution', 'dist'):
        if hasattr(platform, fx):
            sysinfo[fx] = getattr(platform, fx)()
    if 'dist' in sysinfo:
        # only keep the modern variant
        if not 'linux_distribution' in sysinfo:
            sysinfo['linux_distribution'] = sysinfo['dist']
        del sysinfo['dist']
    # system hooks
    distr_info = sysinfo.get('linux_distribution', '')
    if len(distr_info):
        distr_descr = '_describe_%s_system' % distr_info[0].lower()
        if distr_descr in globals():
            globals()[distr_descr](sysinfo)

def _describe_darwin_system(sysinfo):
    for fx in ('mac_ver'):
        if hasattr(platform, fx):
            sysinfo[fx] = getattr(platform, fx)()

def _describe_debian_system(sysinfo):
    pkg_mngr = PkgManager()
    for pkg in ('numpy', 'scipy', 'nibabel', 'apt'):
        sysinfo['pkg_%s' % pkg] = pkg_mngr.get_pkg_info('python-%s' % pkg)

def _describe_ubuntu_system(sysinfo):
    _describe_debian_system(sysinfo)

def get_test_library_paths(prepend=None):
    """Returns a sequence with all configured tets library paths.

    Parameters
    ==========
    prepend : list
      sequence with additional paths that are prepended to the output
    """
    testlibdirs = [os.path.expandvars(tld) for tld in
                      testkraut.cfg.get('library', 'paths',
                              default=opj(os.curdir, 'library')).split(',')]
    # always add the built-in library as a last resort
    testlibdirs.append(opj(os.path.dirname(testkraut.__file__), 'library'))
    if not prepend is None:
        return prepend + testlibdirs
    else:
        return testlibdirs

def get_spec(spec_def, libraries=None):
    """Return a SPEC object from a number of obscure locations.

    SPEC can be given as a string, a path to a SPEC file, or a SPEC
    ID that is search for in any configured library location (plus
    additional libraries passed via ``libraries``).
    """
    spec = None
    # look for the SPEC in any possible library
    for tld in get_test_library_paths(libraries):
        testlib_filepath = opj(tld, spec_def, 'spec.json')
        if os.path.isfile(testlib_filepath):
            lgr.debug("located SPEC for test '%s' in library at '%s'"
                      % (spec_def, tld))
            spec = SPEC(open(testlib_filepath))
            break
        else:
            lgr.debug("did not find SPEC for test '%s' in library at '%s'"
                      % (spec_def, tld))
    if spec is None and os.path.isfile(spec_def):
        # open explicit spec file
        spec = SPEC(open(spec_def))
    if spec is None:
        # spec is given as a str?
        try:
            spec = SPEC(spec_def)
        except ValueError:
            # not a SPEC
            raise ValueError("'%s' is neither a SPEC, or a " % spec_def +
                             "filename of an existing SPEC file, or an ID "
                             "of a test in any of the configured libraries.")
    return spec
