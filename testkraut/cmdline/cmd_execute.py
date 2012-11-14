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
from ..utils import get_spec
import testkraut
from testkraut import cfg

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('spec', metavar='SPEC',
        help="""SPEC filename or testlibary ID""")
    parser.add_argument('-l', '--library', action='append',
            help="""alternative path to a test library. When given, this setting
                 overwrites any library configuration setting""")

def run(args):
    lgr = args.logger
    from .. import runner as tkr
    from ..spec import SPECJSONEncoder
    runner = tkr.LocalRunner(testlibs=args.library)
    # obtain the full SPEC from magic storage
    spec = get_spec(args.spec, args.library)
    try:
        retval = runner(spec)
    finally:
        tbd = runner.get_testbed_dir(spec)
        if os.path.exists(tbd):
            # if we got a testbed, be sure to dump all info that we gathered
            spec.save(opj(tbd, 'spec.json'))
    if not retval:
        lgr.critical("test '%s' failed" % args.spec)
        lgr.info(spec.get('test', {}).get('stdout', ''))
        lgr.info(spec.get('test', {}).get('stderr', ''))
        raise RuntimeError("abort due to test failure")
