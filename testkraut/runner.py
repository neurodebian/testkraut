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

    def _raise(self, exception, why, input=None):
        if not input is None:
            input = ' (got: %s)' % repr(input)
        else:
            input = ''
        raise exception("RUNNER: %s%s" % (why, input))

    def _get_output_path(self, id):
        return os.path.join('_output', id)

    def _proc_input_spec(self, ispecs):
        pass

    def run(self):
        spec = self.spec
        # check the input
        self._proc_input_spec(spec['input spec'])
        # run the actual test command
        command = spec['command']
        ret = None
        if not command is None:
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

    def _proc_output_spec(self, ospecs, ret):
        # assure existing output path
        outdir = self._get_output_path('')
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        # open a logfile
        log_fp = open(self._get_output_path('log'), 'w')
        if not ret is None:
            # if an actual test command was executed
            open(self._get_output_path('retval'), 'w').write(
                    '%i\n' % ret['retval'])
            self._write_line_to_file(self._get_output_path('stdout'),
                                     ret['stdout'])
            self._write_line_to_file(self._get_output_path('stderr'),
                                     ret['stderr'])
            log_fp.write('\n'.join(ret['merged']))
            log_fp.write('\n')

        # loop over all output specs and see what we can handle
        for ospec_id in ospecs:
            ospec = ospecs[ospec_id]
            ospec_path = self._get_output_path(ospec_id)
            if not 'type' in ospec:
                # we don't know what to do with it
                continue
            # a big switch to handle all possible ospec types
            ospec_type = ospec['type']
            if ospec_type == 'shlibdeps':
                self._write_line_to_file(ospec_path,
                                         get_shlibdeps(which(ospec['binary'])))
            elif ospec_type == 'file':
                if hasattr(os, 'link'):
                    if os.path.exists(ospec_path):
                        os.unlink(ospec_path)
                        os.link(ospec['source'], ospec_path)
                else:
                    shutil.copy(ospec['source'], ospec_path)

