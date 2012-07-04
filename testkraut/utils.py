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
import subprocess
import select
import datetime

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
        return [l.strip() for l in ret['stdout']]
