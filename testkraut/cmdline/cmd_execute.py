# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Execute a SPEC.

some more bits...

If no ouput filename is provided (-o) the test result SPEC is written to stdout.

Examples:

$ testkraut execute demo.json

TODO: ADD OUTPUT DESCRIPTION
"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % generate a test SPEC from an arbitrary command call

import logging
lgr = logging.getLogger(__name__)
import argparse
import os
import shutil
import json
import sys
from ..spec import SPECJSONEncoder
from os.path import join as opj
from .helpers import parser_add_common_args

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('spec', metavar='SPEC',
        help="""SPEC filename or testlibary ID""")
    parser_add_common_args(parser, opt=('librarypaths', 'filecache',
                                        'specoutput'))
    parser.add_argument('-t', '--testbed',
            help="""the base directory to run the test in. The actual testbed
                 will be a sub-directory whose name is equal to the test ID.
                 Upon completion of the test this testbed will contain all
                 output data, as well as the test SPEC and logfile(s).""")
    parser.add_argument('--keep-tmp-testbed', action='store_true',
            help="""If set, a temporary testbed will not be deleted upon
                 test completion. Note, custom testbed locations given via
                 --testbed are never deleted.""")

def run(args):
    # local logger
    lgr = args.logger
    import testkraut
    from ..spec import SPECJSONEncoder, SPEC
    from ..utils import get_spec
    # obtain the full SPEC from magic storage
    spec = get_spec(args.spec, args.library)
    # we need to create the testbed directory here, to be able to place the
    # logfile
    tmp_testbedbase = None
    if args.testbed is None:
        import tempfile
        tmp_testbedbase = tempfile.mkdtemp(suffix='', prefix='testkraut')
        args.testbed = tmp_testbedbase
        testbed_path = opj(tmp_testbedbase, spec['id'])
    else:
        testbed_path = opj(args.testbed, spec['id'])
    if args.keep_tmp_testbed or tmp_testbedbase is None:
        # only provide info on testbed location, if it won't be deleted upon
        # completion anyway
        lgr.info('testbed location: %s' % testbed_path)
    if not os.path.exists(testbed_path):
        os.makedirs(testbed_path)
    # configure the logging facility to create a log file in the testbed
    logfile_path = opj(testbed_path, 'testkraut.log')
    logfile = logging.FileHandler(logfile_path)
    logfile.setLevel(args.common_log_level)
    log_format = logging.Formatter(testkraut.cfg.get('logging', 'file format'))
    logfile.setFormatter(log_format)
    # attach log file to the top-level logger
    logging.getLogger('testkraut').addHandler(logfile)
    # and now the runner
    from .. import runner as tkr
    runner = tkr.LocalRunner(testbed_basedir=args.testbed,
                             testlibs=args.library)
    try:
        retval = runner(spec)
    finally:
        if os.path.exists(testbed_path):
            if os.path.exists(logfile_path):
                # suck in the log file if there is any
                spec['test']['log'] = open(logfile_path, 'r').readlines()
            # if we got a testbed, be sure to dump all info that we gathered
            spec.save(opj(testbed_path, 'spec.json'))
            if not args.ospec_filename is None:
                # store a copy to desired custom location
                spec.save(args.ospec_filename)
            else:
                print json.dumps(spec, indent=2, sort_keys=True, cls=SPECJSONEncoder)

    if not tmp_testbedbase is None and not args.keep_tmp_testbed:
        # remove temporary testbed location
        lgr.debug("delete temporary testbed at '%s'" % tmp_testbedbase)
        shutil.rmtree(tmp_testbedbase)
    if not retval:
        lgr.critical("test '%s' failed" % args.spec)
        lgr.info(spec.get('test', {}).get('stdout', ''))
        lgr.info(spec.get('test', {}).get('stderr', ''))
        raise RuntimeError("abort due to test failure")
