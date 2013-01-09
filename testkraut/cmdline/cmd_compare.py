# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Compare a SPEC to a set/population of SPECs.

help=file names of SPECs defining to distribution to compare
                 against.

Examples:

"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % compare a SPEC to a set of other SPECs

import sys
import argparse
import re
from ..spec import SPEC
from .helpers import parser_add_common_args
import numpy as np

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('pop_specs', metavar='SPEC', nargs='+')
    parser.add_argument('-s', '--sample', metavar='SAMPLE', required=True,
            help="sample SPEC file name that shall be compared with other SPECs")
    parser_add_common_args(parser, opt=('include_spec_elements',
                                        'exclude_spec_elements'))

def _walk_tree(samp, pop, proc, comps=None, breadcrumbs=None,
               exclude_elements=None, include_elements=None):
    if breadcrumbs is None:
        breadcrumbs = []
    if isinstance(samp, dict):
        if comps is None:
            comps = {}
        # TODO look if there is a 'version' key and discard items from pop
        # with non-matching values
        for k, v in samp.iteritems():
            pops = [p[k] for p in pop if k in p]
            if len(pops):
                # only dive into it, if we have population samples for this
                # element left
                comp = _walk_tree(v, pops, proc, {}, breadcrumbs + [k],
                                  include_elements=include_elements,
                                  exclude_elements=exclude_elements)
                if not comp is None:
                    comps[k] = comp
        if len(comps):
            # only return a dict if there was any comparision result in it
            return comps
        else:
            return None
    else:
        bc_str = '->'.join(breadcrumbs)
        if not include_elements is None:
            # how often does this location string match any given include
            # expression
            incmatches = sum([not exp.match(bc_str) is None for exp
                                in include_elements])
            if not incmatches > 0:
                # if not at least one matches, skip this one
                return None
        if not exclude_elements is None:
            # how often does this location string match any given exclude
            # expression
            excmatches = sum([not exp.match(bc_str) is None for exp
                                in exclude_elements])
            if excmatches > 0:
                # if at least one matches, skip this one too
                return None
        print bc_str
        # something to compare
        comp = proc(samp, pop)
        # always add the actual observation
        comp['sample_value'] = samp
        return comp

def _spec_comp(samp, pop):
    # big dtype switch
    # implement meaning comparisons for all values that can occur, harrrharrr...
    if isinstance(samp, basestring):
        # nominal label or other text
        return _compare_str(samp, pop)
    elif isinstance(samp, int):
        # rank, version, ...
        return _compare_int(samp, pop)
    elif isinstance(samp, float):
        # metric value
        return _compare_float(samp, pop)
    elif isinstance(samp, list):
        # could be: lists of labels, vectors of same length, arrays of different
        # lengths
        arr = np.array(samp)
        if np.issubdtype(arr.dtype.type, int):
            return _compare_vector_int(samp, pop)
        elif np.issubdtype(arr.dtype.type, float):
            return _compare_vector_float(samp, pop)
        elif np.issubdtype(arr.dtype.type, np.unicode_) or \
             np.issubdtype(arr.dtype.type, np.string_):
            return _compare_list_str(samp, pop)
        else:
            # mixed content
            return _compare_list_str(samp, pop)
    elif samp is None:
        return _compare_none(samp, pop)
    else:
        raise RuntimeError("unhandled datatype '%s'" % type(samp))

def _compare_none(samp, pop):
    return {
            'set': _compare_against_set(samp, pop)
           }

def _compare_str(samp, pop):
    # inputs are essentially labels
    return {
            'set': _compare_against_set(samp, pop)
           }

def _compare_int(samp, pop):
    return {
            'set': _compare_against_set(samp, pop),
            'discrete_dist': _compare_discrete_dist(samp, pop),
           }

def _compare_float(samp, pop):
    return {}

def _compare_vector_int(samp, pop):
    all = {
            'set': _compare_against_set(samp, pop),
            'length': _compare_discrete_dist(len(samp),
                                             [len(p) for p in pop]),
          }
    pop_lengths = set([len(p) for p in pop])
    if len(pop_lengths) == 1 and pop_lengths.pop() == len(samp):
        # all uniform length
        all.update(_compare_same_length_vectors(samp, pop, int))
    return all

def _compare_vector_float(samp, pop):
    all = {}
    pop_lengths = set([len(p) for p in pop])
    if len(pop_lengths) == 1 and pop_lengths.pop() == len(samp):
        # all uniform length
        all.update(_compare_same_length_vectors(samp, pop, int))
    return all


def _compare_list_str(samp, pop):
    return {
            'set': _compare_against_set(samp, pop)
           }

def _compare_same_length_vectors(samp, pop, dtype):
    parr = np.array(pop, dtype=dtype)
    centroid_mean = parr.mean(axis=0)
    centroid_median = np.median(parr, axis=0)
    return {'centroid_mean': centroid_mean,
            'centroid_median': centroid_median,
            }

def _compare_against_set(samp, pop):
    def tupleit(t):
        return tuple(map(tupleit, t)) if isinstance(t, (list, tuple)) else t

    return {'match': (len([None for p in pop if p == samp]),
                      len(pop)),
            'unique': set(tupleit(pop) + (tupleit(samp),))}

def _compare_discrete_dist(samp, pop):
    # create discrete distribution
    # compute probablities
    from collections import defaultdict
    dist_samples = pop
    indi_prob = 1./len(dist_samples)
    probs = defaultdict(float)
    for ds in dist_samples:
        probs[ds] += indi_prob
    from scipy.stats import rv_discrete
    dd = rv_discrete(values=(probs.keys(), probs.values()))
    return {'cdf': dd.cdf(samp),
            'pmf': dd.pmf(samp),
            'pk': dd.pk,
            'xk': dd.xk}

def run(args):
    for argname in ('include_elements', 'exclude_elements'):
        arg = getattr(args, argname)
        if not arg is None:
            try:
                setattr(args, argname, [re.compile(e) for e in arg])
            except re.error:
                raise ValueError("malformed regular expression in %s" % arg)
    sample = SPEC(open(args.sample))
    pop = [SPEC(open(s)) for s in args.pop_specs]
    # filter SPEC with a different version
    pop = [s for s in pop if s.get('version', None) == sample.get('version', '')]
    # traverse the sample SPEC, find the matching pieces in the population and
    # compare
    comps = _walk_tree(sample, pop, _spec_comp,
                       include_elements=args.include_elements,
                       exclude_elements=args.exclude_elements)
    from pprint import pprint
    pprint(comps)
