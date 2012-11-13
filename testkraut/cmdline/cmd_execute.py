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
from testkraut import cfg

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('spec', metavar='SPEC',
        help="""SPEC filename or testlibary ID""")
    parser.add_argument('-l', '--library',
            help="""alternative path to a test library. When given, this setting
                 overwrites any library configuration setting""")

def run(args):
    lgr = args.logger
    from .. import runner as tkr
    from ..spec import SPECJSONEncoder
    runner = tkr.LocalRunner(testlib=args.library)
    # where is the test?
    spec = None
    if not args.library is None:
        testlib_filepath = opj(args.library, args.spec, 'spec.json')
        if os.path.isfile(testlib_filepath):
            # open spec from test library
            lgr.debug("located SPEC for test '%s' in custom location specified by --library" % args.spec)
            spec = SPEC(open(testlib_filepath))
        else:
            lgr.debug("did not find SPEC for test '%s' in custom location specified by --library" % args.spec)
    if args.library is None and spec is None:
        testlibdirs = [os.path.expanduser(tld) for tld in
                          cfg.get('library', 'paths',
                                  default=opj(os.curdir, 'library')).split(',')]
        for tld in testlibdirs:
            testlib_filepath = opj(tld, args.spec, 'spec.json')
            if os.path.isfile(testlib_filepath):
                lgr.debug("located SPEC for test '%s' in library at '%s'"
                          % (args.spec, tld))
                spec = SPEC(open(testlib_filepath))
                break
            else:
                lgr.debug("did not find SPEC for test '%s' in library at '%s'"
                          % (args.spec, tld))
    if spec is None and os.path.isfile(args.spec):
        # open explicit spec file
        spec = SPEC(open(args.spec))
    if spec is None:
        # spec is given as a str?
        try:
            spec = SPEC(args.spec)
        except ValueError:
            # not a SPEC
            raise ValueError("'%s' is neither a SPEC, or a " % args.spec +
                             "filename of an existing SPEC file, or an ID "
                             "of a test in any of the configured libraries.")
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
