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
import re
from ..spec import SPEC
from .helpers import parser_add_common_args

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
    parser.add_argument('--min-abs-numdiff', type=float,
            help="""minimum absolute numerical difference to be considered an
                 actual difference""")
    parser.add_argument('--min-rel-numdiff', type=float,
            help="""minimum relative numerical difference to be considered an
                 actual difference. Differences are evaluated relative to the
                 first input (``from``).""")
    parser.add_argument('--exclude-types', nargs='+',
            choices=('num', 'str', 'seq', 'mis'), default=tuple(),
            help="""exclude one or more types of differences from the output.
                 Possible choices are ``num`` for numerical differences, ``str``
                 for string differences, ``seq`` for sequence diffrences, and
                 ``mis`` for missing or new elements.
                 """)
    parser_add_common_args(parser, opt=('include_spec_elements',
                                        'exclude_spec_elements'))
    parser.add_argument('specs', nargs=2, metavar='SPEC',
            help="SPEC name/identifier")

def print_diff_hdr(fr, to, mode):
    print '%sdiff --%s\n--- %s\n+++ %s' % (style.BRIGHT, mode, fr, to)

def print_diff(breadcrumbs, diffspec, fr, to, exclude_types):
    if 'ndiff' in diffspec:
        if 'str' in exclude_types:
            return
        print_diff_hdr(breadcrumbs, breadcrumbs, 'ndiff')
        for ds in diffspec['ndiff']:
            if ds.startswith('-'):
                print colors.RED + ds,
            elif ds.startswith('+'):
                print colors.GREEN + ds,
            else:
                print colors.CYAN + ds,
    elif 'numdiff' in diffspec:
        if 'num' in exclude_types:
            return
        print_diff_hdr(breadcrumbs, breadcrumbs, 'num')
        print '$ %s' % diffspec['numdiff']
    elif 'seqmatch' in diffspec:
        if 'seq' in exclude_types:
            return
        print_diff_hdr(breadcrumbs, breadcrumbs, 'seq')
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
        if 'mis' in exclude_types:
            return
        frs = tos = breadcrumbs
        if fr is None:
            frs = '(none)'
        if to is None:
            tos = '(none)'
        print_diff_hdr(frs, tos, 'spec')
        if not fr is None:
            print colors.RED + '- %s' % fr
        if not to is None:
            print colors.GREEN + '+ %s' % to

def walk_difftree(dt, fr, to, render, breadcrumbs=None, exclude_types=None,
                  exclude_elements=None, include_elements=None):
    if exclude_types is None:
        exclude_types = tuple()
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
            bc_str = '->'.join(breadcrumbs + [breadcrumb])
            if not include_elements is None:
                # how often does this location string match any given include
                # expression
                incmatches = sum([not exp.match(bc_str) is None for exp
                                    in include_elements])
                if not incmatches > 0:
                    # if not at least one matches, skip this one
                    continue
            if not exclude_elements is None:
                # how often does this location string match any given exclude
                # expression
                excmatches = sum([not exp.match(bc_str) is None for exp
                                    in exclude_elements])
                if excmatches > 0:
                    # if at least one matches, skip this one too
                    continue
            render(bc_str, v, f, t, exclude_types=exclude_types)
        else:
            # walk further
            walk_difftree(v, f, t, render, breadcrumbs + [breadcrumb],
                          exclude_types=exclude_types,
                          include_elements=include_elements,
                          exclude_elements=exclude_elements,
                          )

def run(args):
    for argname in ('include_elements', 'exclude_elements'):
        arg = getattr(args, argname)
        if not arg is None:
            try:
                setattr(args, argname, [re.compile(e) for e in arg])
            except re.error:
                raise ValueError("malformed regular expression in %s" % arg)
    fspec = SPEC(open(args.specs[0]))
    tspec = SPEC(open(args.specs[1]))
    difftree = fspec.diff(tspec,
                          min_abs_numdiff=args.min_abs_numdiff,
                          min_rel_numdiff=args.min_abs_numdiff)
    walk_difftree(difftree, fspec, tspec, print_diff,
                  exclude_types=args.exclude_types,
                  include_elements=args.include_elements,
                  exclude_elements=args.exclude_elements,
                  )
