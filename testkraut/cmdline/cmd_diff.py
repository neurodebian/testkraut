# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Determine the difference between to SPECs.

"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % generate a test SPEC from an arbitrary command call

import sys
import argparse
from ..spec import SPEC

try:
    if not sys.stdout.isatty():
        raise Exception
    from colorama import init
    init(autoreset=True)
    from colorama import Fore as colors
    from colorama import Style as style
except:
    class DummyColors(object):
        def __getattribute__(self, name):
            return ''
    colors = DummyColors()
    style = DummyColors()

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('specs', nargs=2, metavar='SPEC',
            help="SPEC name/identifier")

def print_diff_hdr(fr, to, mode):
    print '%sdiff --%s\n--- %s\n+++ %s' % (style.BRIGHT, mode, fr, to)

def print_diff(breadcrumbs, diffspec, fr, to):
    bc_str = '->'.join(breadcrumbs)
    if 'ndiff' in diffspec:
        print_diff_hdr(bc_str, bc_str, 'ndiff')
        for ds in diffspec['ndiff']:
            if ds.startswith('-'):
                print colors.RED + ds,
            elif ds.startswith('+'):
                print colors.GREEN + ds,
            else:
                print colors.CYAN + ds,
    elif 'numdiff' in diffspec:
        print_diff_hdr(bc_str, bc_str, 'num')
        print '$ %s' % diffspec['numdiff']
    elif 'seqmatch' in diffspec:
        print_diff_hdr(bc_str, bc_str, 'seq')
        for oc in diffspec['seqmatch']:
            if oc[0] == 'equal':
                continue
            print colors.CYAN + '@@ -%i,%i +%i,%i @@' % (oc[1], oc[2] - oc[1],
                                                         oc[3], oc[4] - oc[3])
            if oc[0] in ('delete', 'replace'):
                for el in fr[oc[1]:oc[2]]:
                    print colors.RED + '- %s' % el
            if oc[0] in ('insert', 'replace'):
                for el in to[oc[3]:oc[4]]:
                    print colors.GREEN + '+ %s' % el
    else:
        frs = tos = bc_str
        if fr is None:
            frs = '(none)'
        if to is None:
            tos = '(none)'
        print_diff_hdr(frs, tos, 'spec')
        if not fr is None:
            print colors.RED + '- %s' % fr
        if not to is None:
            print colors.GREEN + '+ %s' % to

def walk_difftree(dt, fr, to, render, breadcrumbs=None):
    if breadcrumbs is None:
        breadcrumbs = []
    for i, k in enumerate(dt):
        if isinstance(dt, dict):
            v = dt[k]
            f = fr.get(k, None)
            t = to.get(k, None)
            breadcrumb = k
        else:
            v = k
            f = fr[i]
            t = to[i]
            breadcrumb = '(%i)' % i
        if not (isinstance(v, dict) or isinstance(v, list)):
            # non-container
            continue
        if isinstance(v, dict) and '%%magic%%' in v and v['%%magic%%'] == 'diff':
            # we found a diff -- render it
            render(breadcrumbs + [breadcrumb], v, f, t)
        else:
            # walk further
            walk_difftree(v, f, t, render, breadcrumbs + [breadcrumb])



def run(args):
    fspec = SPEC(open(args.specs[0]))
    tspec = SPEC(open(args.specs[1]))
    difftree = fspec.diff(tspec)
    walk_difftree(difftree, fspec, tspec, print_diff)
