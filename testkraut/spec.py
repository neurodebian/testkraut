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

import json
import difflib
import numpy as np
from uuid import uuid1 as uuid

__allowed_spec_keys__ = [
        'dependencies',
        'description',
        'entities',
        'environment',
        'evaluations',
        'executables',
        'id',
        'inputs',
        'outputs',
        'processes',
        'system',
        'test',
        'version',
    ]

def _raise(exception, why, input=None):
    if not input is None:
        input = ' (got: %s)' % repr(input)
    else:
        input = ''
    raise exception("SPEC: %s%s" % (why, input))

def _verify_tags(struct, tags, name):
    for tag in tags:
        if not tag in struct:
            _raise(ValueError,
                        "mandatory key '%s' is not in %s" % (tag, name))

def _verify_spec_tags(specs, tags, name):
    for i, os_id in enumerate(specs):
        os = specs[os_id]
        _verify_tags(os, tags, '%s: %s' % (name, os_id))

class SPECJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, np.ndarray):
            return list(o)
        return super(SPECJSONEncoder, self).default(o)

class SPEC(dict):
    def __init__(self, src=None):
        dict.__init__(self)
        if isinstance(src, file):
            self.update(json.load(src))
        elif isinstance(src, basestring):
            self.update(json.loads(src))
        elif isinstance(src, dict):
            self.update(src)
        # charge with sane defaults
        if not 'id' in self:
            self['id'] = uuid().hex
        if not 'version' in self:
            self['version'] = 0
        self._check()

    def _check(self):
        _verify_tags(self, ('id', 'version', 'test'), 'SPEC')
        for i, ev in enumerate(self.get('evaluations', {})):
            _verify_tags(ev, ('id', 'input spec', 'operator'),
                         'evaluation %i' % i)
        _verify_spec_tags(self.get('outputs', {}), ('type', 'value'),
                          'outputs')
        _verify_spec_tags(self.get('inputs', {}), ('type', 'value'),
                          'inputs')

    def __setitem__(self, key, value):
        if not key in __allowed_spec_keys__:
            _raise(ValueError, "refuse to add unsupported key", key)
        if key == 'version':
            if not isinstance(value, int) or value < 0:
                _raise(ValueError,
                    "version needs to be a non-negative integer value "
                    "(got: %s)." % value)
        dict.__setitem__(self, key, value)

    def get(self, *args):
        # check for proper field names
        if len(args) and not args[0] in __allowed_spec_keys__:
            raise ValueError("refuse to access unsupported key", args[0])
        return super(SPEC, self).get(*args)

    def get_hash(self):
        from hashlib import sha1
        str_repr = json.dumps(self, separators=(',',':'), sort_keys=True)
        return sha1(str_repr).hexdigest()

    def save(self, filename):
        spec_file = open(filename, 'w')
        spec_file.write(json.dumps(self, indent=2, sort_keys=True,
                                   cls=SPECJSONEncoder))
        spec_file.write('\n')
        spec_file.close()

    def _get_dict_specs(self, category, spec_type):
        if not category in self:
            return {}
        if spec_type is None:
            return self[category]
        else:
            specs = self[category] 
            return dict([(s, specs[s]) for s in specs if specs[s]['type'] == spec_type])

    def get_inputs(self, type_=None):
        return self._get_dict_specs('inputs', spec_type=type_)

    def get_outputs(self, type_=None):
        return self._get_dict_specs('outputs', spec_type=type_)

    def diff(self, spec, **kwargs):
        return diff(self, spec, **kwargs)


def spec_testoutput_ids(spec):
        return spec.get('outputs', {}).keys()

def diff(fr, to, recursiv_list=False):
    if not type(fr) == type(to):
        # different type
        return {'from': fr, 'to': to, '%%magic%%': 'diff'}
    elif fr is None and to is None:
        return None
    elif isinstance(fr, dict):
        dtree = {}
        # a dict
        fr_keys = set(fr.keys())
        to_keys = set(to.keys())
        # keys in fr but not in to
        for missing in fr_keys - to_keys:
            dtree[missing] = {'from': fr, '%%magic%%': 'diff'}
        # keys in to but not in fr
        for missing in to_keys - fr_keys:
            dtree[missing] = {'to': to, '%%magic%%': 'diff'}
        # compare intersecting keys
        for key in fr_keys.intersection(to_keys):
            value_diff = diff(fr[key], to[key], recursiv_list)
            if not value_diff is None:
                dtree[key] = value_diff
        if len(dtree):
            return dtree
        else:
            return None
    elif isinstance(fr, basestring):
        # any string
        if not fr == to:
            return {'ndiff': difflib.ndiff(('%s\n' % fr).splitlines(True),
                                           ('%s\n' % to).splitlines(True)),
                    '%%magic%%': 'diff'}
        else:
            return None
    elif isinstance(fr, float) or isinstance(fr, int):
        if not fr == to:
            return {'numdiff': to - fr, '%%magic%%': 'diff'}
        else:
            return None
    elif isinstance(fr, list):
        try:
            seqmatch = difflib.SequenceMatcher(None, fr, to).get_opcodes()
        except TypeError:
            raise NotImplementedError(
                "comparing sequences with unhashable values is not supported")
        if not len(seqmatch):
            return None
        elif len(seqmatch) == 1:
            # simple cases
            if seqmatch[0][0] == 'equal':
                # all the same
                return None
            if recursiv_list:
                if seqmatch[0][0] == 'replace':
                    # all different
                    return {'from': fr, 'to': to, '%%magic%%': 'diff'}
                else:
                    # either 'from' or 'to' were empty
                    return {'from': fr, 'to': to, '%%magic%%': 'diff'}
        if recursiv_list and \
            len([None for s in seqmatch
                 if s[0] == 'equal'
                    or (s[0] == 'replace' 
                          and s[2] == s[4] and s[1] == s[3])]) \
            == len(seqmatch):
            # only some values changed, but hopefully no shifts
            out = []
            for s in seqmatch:
                if s[0] == 'equal':
                    out.extend(fr[s[1]:s[2]])
                elif s[0] == 'replace':
                    for i in xrange(s[1], s[2]):
                        out.append(diff(fr[i], to[i], recursiv_list))
                else:
                    # all other conditions should be caught by top-level IF
                    raise RuntimeError('impossible opcode in sequence match')
            return out
        else:
            # complicated
            return {'seqmatch': seqmatch, '%%magic%%': 'diff'}
    raise RuntimeError('unhandled condition is SPEC diff')


