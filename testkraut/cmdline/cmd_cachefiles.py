# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Cache input files requires by test(s).

"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % generate a test SPEC from an arbitrary command call

import argparse
import os
import shutil
from os.path import join as opj
from glob import glob
from ..base import verbose
from ..spec import SPEC
from ..utils import sha1sum

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('ids', nargs='*', metavar='ID',
            help="SPEC name/identifier")
    parser.add_argument('-l', '--library', default='library',
            help="path to the test library")
    parser.add_argument('-c', '--cache', default='filecache',
            help="path to the file cache")
    parser.add_argument('-s', '--search', action='append', default=[],
            help="files to search (wildcardspath to the test library")

def run(args):
    if not len(args.ids):
        # if none specified go through all the SPECs in the lib
        args.ids = [os.path.basename(d) for d in glob(opj(args.library, '*')) if os.path.isdir(d)]
    print args
    wanted_files = set()
    # scan the SPECs of all tests for needed files and their sha1sums
    for test_id in args.ids:
        spec = SPEC(open(opj(args.library, test_id, 'spec.json')))
        for _, input in spec.get_inputs('file').iteritems():
            if 'sha1sum' in input:
                wanted_files.add(input['sha1sum'])
    # what do we have in the cache?
    have_files = [os.path.basename(f) for f in glob(opj(args.cache, '*')) if os.path.isfile(f)]
    # what is missing
    missing_files = wanted_files.difference(have_files)
    search_cache = {}
    # search in all dirs
    for search_dir in args.search:
        for root, dirnames, filenames in os.walk(search_dir):
            for fname in filenames:
                fpath = opj(root, fname)
                sha1 = sha1sum(fpath)
                if sha1 in missing_files:
                    search_cache[sha1] = fpath
    # ensure the cache is there
    if not os.path.exists(args.cache):
        os.makedirs(args.cache)
    # copy/link them into the cache
    for sha1, fpath in search_cache.iteritems():
        dst_path = opj(args.cache, sha1)
        done = False
        if hasattr(os, 'symlink'):
            os.symlink(fpath, dst_path)
        elif hasattr(os, 'link'):
            try:
                print 'LINK'
                os.link(fpath, dst_path)
                print 'POSTLINK'
            except OSError:
                raise
                # silently fail if linking doesn't work (e.g.
                # cross-device link ... will recover later
                shutil.copy(fpath, dst_path)
        else:
            shutil.copy(fpath, dst_path)
