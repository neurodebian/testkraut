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
import shutil
from .utils import run_command, get_shlibdeps, which

class Runner(object):
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
        return os.path.join('_output', id)

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
        self._proc_input_spec(spec['input spec'])
        # run the actual test command
        command = spec['command']
        ret = None
        if not command is None:
            self._log("Run test command [%s]" % command)
            ret = run_command(command)
        # handle test output
        self._proc_output_spec(spec['output spec'], ret)
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

