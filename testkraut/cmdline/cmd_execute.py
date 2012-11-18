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
import sys
from os.path import join as opj
from .helpers import parser_add_common_args

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('spec', metavar='SPEC',
        help="""SPEC filename or testlibary ID""")
    parser_add_common_args(parser, opt=('librarypaths',))
    parser.add_argument('-t', '--testbeds', default='testbeds',
            help="""base path of all test beds""")

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
    testbed_path = opj(args.testbeds, spec['id'])
    if not os.path.exists(testbed_path):
        os.makedirs(testbed_path)
    # configure the logging facility to create a log file in the testbed
    logfile = logging.FileHandler(opj(testbed_path, 'testkraut.log'))
    logfile.setLevel(args.common_log_level)
    log_format = logging.Formatter(testkraut.cfg.get('logging', 'file format'))
    logfile.setFormatter(log_format)
    # attach log file to the top-level logger
    logging.getLogger('testkraut').addHandler(logfile)
    # and now the runner
    from .. import runner as tkr
    runner = tkr.LocalRunner(testlibs=args.library)
    try:
        retval = runner(spec)
    finally:
        if os.path.exists(testbed_path):
            # if we got a testbed, be sure to dump all info that we gathered
            spec.save(opj(testbed_path, 'spec.json'))
    if not retval:
        lgr.critical("test '%s' failed" % args.spec)
        lgr.info(spec.get('test', {}).get('stdout', ''))
        lgr.info(spec.get('test', {}).get('stderr', ''))
        raise RuntimeError("abort due to test failure")
