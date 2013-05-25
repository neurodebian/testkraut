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
from os.path import join as opj
import re
import shutil
from datetime import datetime
from uuid import uuid1 as uuid
from . import utils
from . import evaluators
from .utils import run_command, get_shlibdeps, which, sha1sum, \
        get_script_interpreter, describe_system, get_test_library_paths
from .pkg_mngr import PkgManager
from .spec import SPEC
import testkraut
from testkraut import cfg
import logging
lgr = logging.getLogger(__name__)

def check_file_hash(filespec, filepath):
    """Check the hash of a file given a file SPEC

    If not target hash is present in the file SPEC ``None`` is returned.
    Otherwise a boolean return value indicated whether the hash matches.
    """
    for hashtype in ('md5sum', 'sha1sum'):
        if hashtype in filespec:
            targethash = filespec[hashtype]
            hasher = getattr(utils, hashtype)
            observedhash = hasher(filepath)
            if targethash != observedhash:
                lgr.debug("hash for '%s' does not match ('%s' != '%s')"
                          % (filepath, observedhash, targethash))
                return False
            else:
                lgr.debug("hash for '%s' matches ('%s')"
                          % (filepath, observedhash))
                return True
    lgr.debug("no hash for '%s' found" % filepath)
    return None

def locate_file_in_cache(filespec, cache):
    """Very simple cache lookup -- to be replaced with proper cache object"""
    if filespec is None:
        filespec = dict()
    if not 'sha1sum' in filespec:
        # nothing we can do
        return None
    cand_filename = opj(cache, filespec['sha1sum'])
    if os.path.isfile(cand_filename):
        return cand_filename
    lgr.debug("hash '%s' not present in cache '%s'"
              % (filespec['sha1sum'], cache))
    return None

def place_file_into_dir(filespec, dest_dir, search_dirs=None, cache=None,
                        force_overwrite=True):
    """Search for a file given a SPEC and place it into a destination directory

    Parameters
    ----------
    filespec : SPEC dict
      Dictionary with information on the file, keys could be, e.g., 'value',
      'type', or 'sha1sum'.
    dest_dir : path
      Path of the destination/target directory
    search_dirs : None or sequence
      If not None, a sequence of local directories to be searched for the
      desired file
    cache : None or path
      If not None, a path to a file cache directory where the desired file is
      searched by its sha1sum (if present in the SPEC)
    """
    # TODO refactor from simple cachedir to cache object that could also obtain
    # a file from remote locations

    # sanity
    if not 'type' in filespec or filespec['type'] != 'file':
        raise ValueError("expected SPEC is not a file SPEC, got : '%s'"
                         % filespec)

    fname = filespec['value']
    # this will be the discovered file path
    fpath = None
    # first try the cache
    if fpath is None and not cache is None:
        lgr.debug("looking for '%s' in the cache" % fname)
        fpath = locate_file_in_cache(filespec, cache)
    if not search_dirs is None:
        lgr.debug("cache lookup for '%s' unsuccessful, trying local search"
                  % fname)
        for ldir in search_dirs:
            cand_path = opj(ldir, fname)
            if not os.path.isfile(cand_path):
                lgr.debug("could not find file '%s' in '%s'" % (fname, ldir))
                continue
            lgr.debug("found file '%s' in '%s'" % (fname, ldir))
            hashmatch = check_file_hash(filespec, cand_path)
            if hashmatch in (True, None):
                fpath = cand_path
                break
    if fpath is None:
        # out of ideas
        raise LookupError("cannot find file matching spec %s" % filespec)
    # get the file into the dest_dir
    dest_fname = opj(dest_dir, fname)
    if force_overwrite or not os.path.isfile(dest_fname):
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy(fpath, dest_fname)
    else:
        lgr.debug("skip copying already present file '%s'" % fname)


def prepare_local_testbed(spec, dst, search_dirs, cache=None,
                          force_overwrite=True):
    inspecs = spec.get('inputs', {})
    # locate and copy test input into testbed
    for inspec_id in inspecs:
        inspec = inspecs[inspec_id]
        type_ = inspec['type']
        if type_ == 'file':
            place_file_into_dir(inspec, dst,
                                search_dirs=search_dirs, cache=cache,
                                force_overwrite=force_overwrite)
        else:
            raise ValueError("unknown input spec type '%s'" % type_)
