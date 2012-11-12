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

$ testkraut generate --id demo -o test.spec -- bash -c "cat spec.json > newstuff"

TODO: ADD OUTPUT DESCRIPTION
"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % generate a test SPEC from an arbitrary command call

import argparse
import os
import re
import itertools
from os.path import join as opj
from ..spec import SPEC
from ..utils import sha1sum, get_cmd_prov_strace, guess_file_tags
from ..pkg_mngr import PkgManager

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
        help="do not use strace to analyze software and data dependencies.")
    parser.add_argument(
        '--ignore-outputs',
        help="regular expression matching command output filenames/paths to ignore.")
    parser.add_argument(
        '--match-outputs',
        help="""regular expression matching command output filenames/paths to
             consider in the SPEC -- ignore all others.""")
    parser.add_argument(
        '--match-cmds', default=r'.*', metavar='REGEX',
        help="regular expression matching commands to capture as test components.")
    parser.add_argument(
        '--nomin', '--no-minimize-inputs', action='store_true', dest='no_minimize_inputs',
        help="""always include all files present in the test directory as input
             files, regardless of whether they are actually used during
             execution. This option only has an effect when strace is used. If it
             is not available, no minimization is performed anyway. If strace is
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
        dir_content += [(fn, sha1sum(fn)) for fn in dirfiles if os.path.isfile(fn)]
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

def _proc_generates(procs, proc, starts, filter=None, ignore=None):
    generated = proc.get('generates', [])
    if len(generated):
        if not ignore is None:
            generated = [g for g in generated if ignore.match(g) is None]
        if not filter is None:
            generated = [g for g in generated if not filter.match(g) is None]
        if len(generated):
            # still files left?
            return True
    for started_pid in starts[proc['pid']]:
        generates = _proc_generates(procs, procs[started_pid], starts,
                                    filter=filter, ignore=ignore)
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

    # try using a local package manager to obtain more info on software deps
    pkg_mngr = PkgManager()

    # assume execution within the testbed
    testbed_dir = os.path.abspath(os.curdir)
    # get the state of the union
    prior_test_hashes = get_dir_hashes(testbed_dir)
    # run through strace
    proc_info, retval = get_cmd_prov_strace(args.arg, args.match_cmds)
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
                processes={},
                executables={},
                environment={},
                test={},
                inputs={},
                outputs={},
                evaluations={}))

    # in case of a shell command
    spec['test'] = dict(type='shell_command', command=args.arg)
    # filter files
    if not args.ignore_outputs is None:
        args.ignore_outputs = re.compile(args.ignore_outputs)
    if not args.match_outputs is None:
        args.match_outputs = re.compile(args.match_outputs)
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
        if (not args.ignore_outputs is None and not args.ignore_outputs.match(relname) is None) \
           or (not args.match_outputs is None and args.match_outputs.match(relname) is None):
            # skip
            continue
        s = dict(type='file', value=relname,
                 tags=list(guess_file_tags(relname)))
        spec['outputs'][relname] = s

    # and now get all info into the SPEC
    dep_mapper = {}
    spec['dependencies'] = dep_mapper
    proc_mapper = {}
    spec['processes'] = proc_mapper
    exec_mapper = {}
    spec['executables'] = exec_mapper
    pid_counter = 0
    pid_native2new = {}
    exec2pkg = set()
    # which processes are (indirectly) involved in some sort of output generation
    effective_pids = [proc['pid'] for pid, proc in proc_info.iteritems()
                        if _proc_generates(proc_info, proc, starts,
                           ignore=args.ignore_outputs,
                           filter=args.match_outputs)]
    for pid, proc in proc_info.iteritems():
        if not pid in effective_pids:
            # skip all procs that do not generate or start something that generates
            continue
        # discover the corresponding executable
        executable = os.path.realpath(proc['executable'])
        espec = dict()
        exec_mapper[executable] = espec
        # make a record of this process
        pspec = dict(executable=executable,
                     #pid=pid_counter, argv=proc['argv'])
                     argv=proc['argv'])
        for ftype in ('uses', 'generates'):
            flist = proc.get(ftype, [])
            if len(flist):
                pspec[ftype] = [os.path.relpath(fn) for fn in flist if os.path.isfile(fn)]
        if 'started_by' in proc:
            pspec['started_by'] = proc['started_by']
        proc_mapper[pid_counter] = pspec
        ## map old to new PID
        pid_native2new[proc['pid']] = pid_counter
        pid_counter += 1
        if not executable in exec2pkg:
            # we haven't seen this binary yet
            pkgname = pkg_mngr.get_pkg_name(executable)
            if not pkgname is None:
                pkg_deps = dep_mapper.get(pkg_mngr.get_platform_name(), set())
                pkg_deps.add(pkgname)
                dep_mapper[pkg_mngr.get_platform_name()] = pkg_deps
            exec2pkg.add(executable)
    ## 2nd pass -- store inter-process deps using new/simplified PIDs
    for pid, proc in proc_mapper.iteritems():
        if not 'started_by' in proc:
            continue
        native_parent_pid = proc['started_by']
        if native_parent_pid is None:
            # this is the mother process
            continue
        proc['started_by'] = pid_native2new[native_parent_pid]
    if 'deb' in dep_mapper:
        # do a dpkg style dependency statement
        dep_mapper['deb'] = ' ,'.join(dep_mapper['deb'])
    # record full environment (if desired)
    if not args.dump_env is None:
        for env in os.environ:
            if not re.match(args.dump_env, env) is None:
                spec['environment'][env] = {}
    spec.save(args.spec_filename)
