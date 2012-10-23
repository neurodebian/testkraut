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
from ..utils import sha1sum
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
        '--sv', '--spec-version', default=0, type=int, dest='spec_version',
        metavar='VERSION', help="SPEC version")
    parser.add_argument(
        '--env', '--dump-environment', action='store_true', dest='dump_env',
        help="dump all environment variables into the SPEC")
    parser.add_argument(
        '--no-cde', action='store_true',
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


def run(args):
    import sys
    import subprocess
    import tempfile
    import re
    import shutil
    import json

    # try using APT to obtain more info on software deps
    try:
        import apt_pkg
        apt_pkg.init_config()
        apt_pkg.init_system()
        apt = apt_pkg.Cache()
    except:
        apt = None

    # assume execution within the testbed
    testbed_dir = os.path.abspath(os.curdir)
    # get the state of the union
    prior_test_hashes = get_dir_hashes(testbed_dir, ignore=['cde.options'])

    if args.no_cde:
        retcode = 1
    else:
        # make an attempt to run cmd within CDE
        wdir = tempfile.mkdtemp(prefix='tkraut_genspec')
        cde_args = ['cde', '-o', wdir]
        cde_args += args.arg
        try:
            retcode = subprocess.call(cde_args,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        except OSError:
            retcode = 1

    if retcode == 0:
        cde_root = opj(wdir, 'cde-root')
        # this needs somebody with windows foo to check for a way to do this on that
        # platform
        cde_testbed_dir = opj(cde_root, testbed_dir[1:])
        with_cde = True
    else:
        # no need to keep the working dir
        if not args.no_cde:
            shutil.rmtree(wdir)
        verbose(1, "No result from CDE execution. Attempting native run.")
        retcode = subprocess.call(args.arg,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        with_cde = False
        if retcode != 0:
            raise ValueError("command '%s' returned with non-zero exit code" % args.arg)

    # testbed content after run
    post_test_hashes = get_dir_hashes(testbed_dir, ignore=['cde.options'])
    # categorize testbed content
    new_files = set(post_test_hashes).difference(prior_test_hashes)
    deleted_files = set(prior_test_hashes).difference(post_test_hashes)
    changed_files = [fn for fn in prior_test_hashes if not fn in deleted_files and prior_test_hashes[fn] != post_test_hashes[fn]]

    # software dependencies
    soft_deps = []
    if with_cde:
        for te in find_executables(cde_root):
            dname, fname = os.path.split(te)
            if fname.endswith('.so'):
                # plugin?
                continue
            if fname.endswith('.cde'):
                # cde internal
                continue
            if re.match(r'.*\.so\.[0-9]+', fname):
                # unix library
                continue
            exec_path = opj(dname[len(cde_root):], fname)
            soft_deps.append(exec_path)

    # software dependencies
    data_deps = []
    if with_cde:
        for tf in find_files(cde_testbed_dir):
            if tf.endswith('.cde'):
                # cde internal
                continue
            data_deps.append(tf[len(cde_testbed_dir) + 1:])

    # cleanup
    if with_cde:
        #shutil.rmtree(wdir)
        os.unlink('cde.options')
    # spec skeleton
    spec = dict(id=args.id,
                description=args.description,
                version=args.spec_version,
                dependencies=[],
                test={},
                input_specs={},
                output_specs={},
                evaluations=[])
    # in case of a shell command
    spec['test'] = dict(type='shell_command', command=args.arg)
    # record al input files
    for ipf in prior_test_hashes:
        relname = os.path.relpath(ipf)
        if with_cde and not args.no_minimize_inputs and not relname in data_deps:
            continue
        s = dict(type='file', value=relname,
                 sha1sum=prior_test_hashes[ipf])
        spec['input_specs'][relname] = s
    # record all output files
    for opf in new_files:
        relname = os.path.relpath(opf)
        s = dict(type='file', value=relname)
        spec['output_specs'][relname] = s
    # record all used executables
    for exe in soft_deps:
        s = dict(type='executable', path=exe)
        try:
            # provide by a Debian package?
            dpkg = subprocess.Popen(['dpkg', '-S', exe],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            dpkg.wait()
            pkgname = None
            for line in dpkg.stdout:
                lspl = line.split(':')
                if lspl[0].count(' '):
                    continue
                pkgname = lspl[0]
            if not pkgname is None:
                s['debian'] = dict(package=pkgname)
                if not apt is None:
                    s['debian']['version'] = apt[pkgname].current_ver.ver_str
        except OSError:
            pass
        spec['dependencies'].append(s)
    # record full environment (if desired)
    if args.dump_env:
        for env in os.environ:
            s = dict(type='envvar', name=env, value=os.environ[env])
            spec['dependencies'].append(s)

    spec_file = open(args.spec_filename, 'w')
    spec_file.write(json.dumps(spec, indent=2))
    spec_file.write('\n')
    spec_file.close()
