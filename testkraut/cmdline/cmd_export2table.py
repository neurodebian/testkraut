# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Export data from several SPECs into a table.
"""

__docformat__ = 'restructuredtext'

# magic line for manpage summary
# man: -*- % generate a test SPEC from an arbitrary command call

import argparse
from ..spec import SPEC

parser_args = dict(formatter_class=argparse.RawDescriptionHelpFormatter)

def setup_parser(parser):
    parser.add_argument('specs', nargs='+', metavar='SPEC',
            help="SPEC filenames")
    parser.add_argument('-c', '--column', action='append', nargs='+',
            default=list(), required=True, metavar='ARG',
            help="column definition (data field, name, transform)")
    parser.add_argument('--csv', metavar='FILENAME',
            help='store table in CSV format into a file')
    parser.add_argument('--numtxt', metavar='FILENAME',
            help='store table in TXT format into a file')

def op2fx(op):
    if op == 'v':
        # unmodified
        return lambda x: x
    if op == 'len':
        return len
    else:
        raise ValueError("unknown operator")

def parse_column_def(coldef):
    ptr = header = None
    transform = lambda x: x
    deflen = len(coldef)
    ptr = coldef[0].split('->')
    # TODO implement a way to access list elements too
    if deflen > 1:
        header = coldef[1]
    if deflen > 2:
        transform = op2fx(coldef[2])
    return ptr, header, transform

def get_nested_value(dct, ptr, entities):
    if len(ptr):
        if ptr[0] == 'entity':
            # look whether an entity is references (implicitely)
            entity = dct['entity']
            if entity in entities:
                # reroute
                ptr[0] = entity
                dct = entities
        elif isinstance(dct, list) and ptr[0].isdigit():
            # index a list
            entity = dct[int(ptr[0])]
            if entity in entities:
                # reroute
                ptr[0] = entity
                dct = entities
        elif isinstance(dct, basestring):
            if dct in entities:
                # reroute
                ptr = [dct] + ptr
                dct = entities
        return get_nested_value(dct[ptr[0]], ptr[1:], entities)
    else:
        return dct

def export_as_csv(fname, rows, hdrs):
    import csv
    writer = csv.writer(open(fname, 'wb'), quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(hdrs)
    writer.writerows(rows)

def export_as_txt(fname, rows):
    from numpy import savetxt
    savetxt(fname, rows)

def run(args):
    coldefs = [parse_column_def(cd) for cd in args.column]
    # column headers
    hdrs = [c[1] for c in coldefs]
    rows = []
    for spec_fname in args.specs:
        spec = SPEC(open(spec_fname))
        row = [None] * len(coldefs)
        for i, c in enumerate(coldefs):
            try:
                val = get_nested_value(spec, c[0], spec.get('entities', {}))
                # transform
                val = c[2](val)
            except KeyError:
                print "Skipping '%s' in '%s' (field not found)" % ('->'.join(c[0]), spec_fname)
                val = None
            row[i] = val
        rows.append(row)
    if not args.csv is None:
        export_as_csv(args.csv, rows, hdrs)
    if not args.numtxt is None:
        try:
            export_as_txt(args.numtxt, rows)
        except TypeError:
            raise ValueError("failed to write an unsupported data type into '%s'" % args.numtxt)
    # TODO pytables/pandas support


