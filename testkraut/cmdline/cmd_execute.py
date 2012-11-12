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

import argparse
import os
import sys
from os.path import join as opj
from ..spec import SPEC

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('spec', metavar='SPEC',
        help="""SPEC filename or testlibary ID""")
    parser.add_argument('-l', '--library', default='library',
            help="path to the test library")

def run(args):
    from .. import runner as tkr
    from ..spec import SPECJSONEncoder
    runner = tkr.LocalRunner(testlib=args.library)
    # where is the test?
    testlib_filepath = opj(args.library, args.spec, 'spec.json')
    if os.path.isfile(testlib_filepath):
        # open spec from test library
        spec = SPEC(open(testlib_filepath))
    elif os.path.isfile(args.spec):
        # open explicit spec file
        spec = SPEC(open(args.spec))
    else:
        # spec is given as a str?
        spec = SPEC(args.spec)
    try:
        retval, spec = runner(spec)
    finally:
        spec.save(opj(runner.get_testbed_dir(spec), 'spec.json'))
    if not retval:
        args.logger.critical("test '%s' failed" % args.spec)
        args.logger.info(spec.get('test', {}).get('stdout', ''))
        args.logger.info(spec.get('test', {}).get('stderr', ''))
        
        raise RuntimeError("abort due to test failure")
