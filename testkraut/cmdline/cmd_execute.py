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
from os.path import join as opj

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
    retval, spec = runner(args.spec)
    spec.save(opj(runner.get_testbed_dir(spec), 'spec.json'))
