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
import urllib2
from os.path import join as opj
from glob import glob
from ..spec import SPEC
from ..utils import sha1sum, get_test_library_paths, get_spec
from testkraut import cfg

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('ids', nargs='*', metavar='ID',
            help="SPEC name/identifier")
    parser.add_argument('-l', '--library', action='append', default=[],
            help="""path to an additional test library""")
    parser.add_argument('-c', '--cache', default='filecache',
            help="path to the file cache")
    parser.add_argument('-s', '--search', action='append', default=[],
            help="where to search for files")
    parser.add_argument('--copy', action='store_true',
            help="copy files into the cache instead of symlinking them")

def run(args):
    lgr = args.logger
    if not len(args.ids):
        # if none specified go through all the SPECs in the lib
        args.ids = []
        for tld in get_test_library_paths(args.library): 
            args.ids.extend([os.path.basename(d)
                                for d in glob(opj(tld, '*'))
                                        if os.path.isdir(d)])
    wanted_files = set()
    hash_lookup = {}
    # scan the SPECs of all tests for needed files and their sha1sums
    for test_id in args.ids:
        lgr.debug("scan required files for test '%s'" % test_id)
        spec = get_spec(test_id, args.library)
        for _, input in spec.get_inputs('file').iteritems():
            if 'sha1sum' in input:
                wanted_files.add(input['sha1sum'])
                hash_lookup[input['sha1sum']] = (test_id, input.get('value', ''))
                lgr.debug("add '%s' (%s) to the list of files to look for"
                          % (input.get('value', ''), input['sha1sum']))
    # what do we have in the cache?
    have_files = [os.path.basename(f) for f in glob(opj(args.cache, '*')) if os.path.isfile(f)]
    # what is missing
    missing_files = wanted_files.difference(have_files)
    search_cache = {}
    # search in all locale dirs
    for search_dir in (args.search + args.library):
        for root, dirnames, filenames in os.walk(search_dir):
            for fname in filenames:
                fpath = opj(root, fname)
                sha1 = sha1sum(fpath)
                if sha1 in missing_files:
                    # make path relative to cache dir
                    search_cache[sha1] = os.path.relpath(fpath, args.cache)
                    lgr.debug("found missing '%s' at '%s'" % (sha1, fpath))
    # ensure the cache is there
    if not os.path.exists(args.cache):
        os.makedirs(args.cache)
    # try downloading missing files from the web
    hashpots = cfg.get('hash stores', 'http').split()
    for sha1 in missing_files.copy():
        for hp in hashpots:
            try:
                urip = urllib2.urlopen('%s%s' % (hp, sha1))
                dst_path = opj(args.cache, sha1)
                fp = open(dst_path, 'wb')
                lgr.debug("download '%s%s'->'%s'" % (hp, sha1, dst_path))
                fp.write(urip.read())
                fp.close()
                missing_files.remove(sha1)
                break
            except urllib2.HTTPError:
                lgr.debug("cannot find '%s' at '%s'" % (sha1, hp))
    # copy/link them into the cache
    for sha1, fpath in search_cache.iteritems():
        dst_path = opj(args.cache, sha1)
        if os.path.lexists(dst_path):
            if os.path.islink(dst_path):
                # remove existing symlink
                os.remove(dst_path)
                lgr.debug("removing existing symlink '%s' in filecache"
                          % dst_path)
            else:
                lgr.warning(
                    "Will not replace existing non-symlink cache content: [%s: %s (%s)]"
                    % (hash_lookup[sha1] + (sha1,)))
        if not args.copy:
            os.symlink(fpath, dst_path)
            lgr.debug("symlink '%s'->'%s'" % (fpath, dst_path))
        elif hasattr(os, 'link'):
            # be nice and try hard-linking
            try:
                os.link(fpath, dst_path)
                lgr.debug("hardlink '%s'->'%s'" % (fpath, dst_path))
            except OSError:
                # silently fail if linking doesn't work (e.g.
                # cross-device link ... will recover later
                shutil.copy(fpath, dst_path)
                lgr.debug("copylink '%s'->'%s'" % (fpath, dst_path))
        else:
            shutil.copy(fpath, dst_path)
            lgr.debug("copylink '%s'->'%s'" % (fpath, dst_path))
        missing_files.remove(sha1)
    if len(missing_files):
        lgr.warning('cannot find needed file(s):')
        for mf in missing_files:
            lgr.warning('  %s: %s (%s)' % (hash_lookup[mf] + (mf,)))
