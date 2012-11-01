# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Generate a test specification from an arbitrary command call.

some more bits...

Doesn't work nicely when input data is under /tmp

Examples:

$ testkraut genspec --id demo -o test.spec -- bash -c "cat spec.json > newstuff"

TODO: ADD OUTPUT DESCRIPTION
"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % generate a test SPEC from an arbitrary command call

import argparse
import os
import itertools
from os.path import join as opj
from ..spec import SPEC
from ..utils import sha1sum, get_debian_pkgname, get_debian_pkginfo, \
                    get_cmd_prov_strace, guess_file_tags
from ..base import verbose

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument(
        '-o', '--spec-file', required=True, metavar='FILENAME', dest='spec_filename',
        help="name of the output SPEC file")
    parser.add_argument(
        '--id', required=True,
        help="SPEC name/identifier")
    parser.add_argument(
        '--description', default='',
        help="SPEC description")
    parser.add_argument(
        '--author', default='', nargs=2,
        help="SPEC author given as <'NAMES' EMAIL>")
    parser.add_argument(
        '--sv', '--spec-version', default=0, type=int, dest='spec_version',
        metavar='VERSION', help="SPEC version")
    parser.add_argument(
        '--env', '--dump-environment', metavar='REGEX', dest='dump_env',
        help="""dump all environment variables into the SPEC whose names match
             the regular expression""")
    parser.add_argument(
        '--no-strace', action='store_true',
        help="do not use CDE to analyze software and data dependencies.")
    parser.add_argument(
        '--nomin', '--no-minimize-inputs', action='store_true', dest='no_minimize_inputs',
        help="""always include all files present in the test directory as input
             files, regardless of whether they are actually used during
             execution. This option only has an effect when CDE is used. If it
             is not available, no minimization is performed anyway. If CDE is
             not able to properly track file access, resulting in insufficent
             input SPECs, enable the option.""")
    parser.add_argument('arg', nargs='+', metavar='ARGS',
        help="""command or workflow filename""")

def get_dir_hashes(path, ignore=None):
    if ignore is None:
        ignore = []
    dir_content = []
    for dirlist in os.walk(path):
        tocheck = [fn for fn in dirlist[2] if not fn in ignore]
        nfiles = len(tocheck)
        dirfiles = [fn for fn in itertools.imap(opj,
                                                [dirlist[0]] * nfiles,
                                                tocheck)]
        dir_content += [(fn, sha1sum(fn)) for fn in dirfiles]
    return dict(dir_content)

def find_executables(path):
    executables = []
    for dirlist in os.walk(path):
        for fn in dirlist[2]:
            testfile = opj(dirlist[0], fn)
            if os.path.isfile(testfile) and os.access(testfile, os.X_OK):
                executables.append(testfile)
    return executables

def find_files(path):
    files = []
    for dirlist in os.walk(path):
        for fn in dirlist[2]:
            testfile = opj(dirlist[0], fn)
            if os.path.isfile(testfile):
                files.append(testfile)
    return files

def _proc_generates(procs, proc, starts):
    if len(proc['generates']):
        return True
    for started_pid in starts[proc['pid']]:
        generates = _proc_generates(procs, procs[started_pid], starts)
        if generates:
            return True
    return False

def run(args):
    import sys
    import subprocess
    import tempfile
    import re
    import shutil
    import json

    # try using APT to obtain more info on software deps
    #try:
    #    import apt
    #    apt = apt.Cache()
    #except:
    #    apt = None

    # assume execution within the testbed
    testbed_dir = os.path.abspath(os.curdir)
    # get the state of the union
    prior_test_hashes = get_dir_hashes(testbed_dir)
    # run through strace
    proc_info, retval = get_cmd_prov_strace(args.arg)
    if not retval == 0:
        raise RuntimeError('command returned with non-zero exit code %s'
                           % args.arg)
    used_files = set()
    starts = dict(zip([p['pid'] for p in proc_info.values()],
                      [list() for i in xrange(len(proc_info))]))
    for proc in proc_info.values():
        used_files = used_files.union(proc['uses'])
        if not proc['started_by'] is None:
            starts[proc['started_by']].append(proc['pid'])
    # testbed content after run
    post_test_hashes = get_dir_hashes(testbed_dir)
    # categorize testbed content
    new_files = set(post_test_hashes).difference(prior_test_hashes)
    deleted_files = set(prior_test_hashes).difference(post_test_hashes)
    changed_files = [fn for fn in prior_test_hashes if not fn in deleted_files and prior_test_hashes[fn] != post_test_hashes[fn]]

    # spec skeleton
    spec = SPEC(
            dict(id=args.id,
                description=args.description,
                version=args.spec_version,
                components=[],
                test={},
                inputs={},
                outputs={},
                evaluations=[]))

    # in case of a shell command
    spec['test'] = dict(type='shell_command', command=args.arg)
    # record al input files
    for ipf in prior_test_hashes:
        relname = os.path.relpath(ipf)
        if not relname in used_files:
            # skip
            continue
        s = dict(type='file', value=relname,
                 sha1sum=prior_test_hashes[ipf],
                 tags=list(guess_file_tags(relname)))
        spec['inputs'][relname] = s
    # record all output files
    for opf in new_files:
        relname = os.path.relpath(opf)
        s = dict(type='file', value=relname,
                 tags=list(guess_file_tags(relname)))
        spec['outputs'][relname] = s

    # 1st pass -- store info on individual test components
    proc_mapper = {}
    pid_counter = 0
    deb_pkg_cache = {}
    for pid, proc in proc_info.iteritems():
        executable = os.path.realpath(proc['executable'])
        s = dict(type='process', executable=dict(path=executable),
                 pid=pid_counter, argv=proc['argv'])
        pid_counter += 1
        if executable in deb_pkg_cache:
            s['executable']['providers'] = [deb_pkg_cache[executable]]
        else:
            pkgname = get_debian_pkgname(executable)
            debinfo = None
            if not pkgname is None:
                pkginfo = dict(name=pkgname, type='debian_pkg')
                s['executable']['providers'] = [pkginfo]
            deb_pkg_cache[executable] = debinfo
        proc_mapper[proc['pid']] = s
    # 2nd pass -- store inter-process/file dependencies
    for pid, proc in proc_mapper.iteritems():
        pinfo = proc_info[pid]
        for ftype in ('uses', 'generates'):
            flist = pinfo.get(ftype, [])
            if len(flist):
                proc[ftype] = [os.path.relpath(fn) for fn in flist if os.path.isfile(fn)]
        native_parent_pid = pinfo['started_by']
        if native_parent_pid is None:
            # this is the mother process
            continue
        parent_proc_pid = proc_mapper[native_parent_pid]['pid']
        proc['started_by'] = parent_proc_pid
    # 3rd pass -- only store processes that are involved in some sort of file
    # generation
    effective_pids = []
    for pid, proc in proc_mapper.iteritems():
        if _proc_generates(proc_info, proc_info[pid], starts):
            effective_pids.append(proc['pid'])
            spec['components'].append(proc)
    # 4th pass -- beautify PIDs
    pid_mapper = dict(zip(effective_pids, range(len(effective_pids))))
    for cmd_spec in spec['components']:
        cmd_spec['pid'] = pid_mapper[cmd_spec['pid']]
        if 'started_by' in cmd_spec:
            cmd_spec['started_by'] = pid_mapper[cmd_spec['started_by']]
    # record full environment (if desired)
    if not args.dump_env is None:
        for env in os.environ:
            if not re.match(args.dump_env, env) is None:
                s = dict(type='envvar', name=env)
                spec['components'].append(s)
    spec.save(args.spec_filename)
