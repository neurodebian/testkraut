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
import numpy as np

__allowed_spec_keys__ = [
        'test',
        'components',
        'description',
        'id',
        'inputs',
        'outputs',
        'version',
        'evaluations',
        'entities'
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
        self._check()

    def _check(self):
        _verify_tags(self, ('id', 'version'), 'SPEC')
        for i, ev in enumerate(self.get('evaluations', [])):
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

    def _get_list_specs(self, category, spec_type):
        if spec_type is None:
            return self[category]
        else:
            return [d for d in self[category] if d['type'] == spec_type]

    def _get_dict_specs(self, category, spec_type):
        if spec_type is None:
            return self[category]
        else:
            specs = self[category] 
            return dict([(s, specs[s]) for s in specs if specs[s]['type'] == spec_type])

    def get_components(self, type_=None):
        return self._get_list_specs('components', spec_type=type_)

    def get_inputs(self, type_=None):
        return self._get_dict_specs('inputs', spec_type=type_)

    def get_outputs(self, type_=None):
        return self._get_dict_specs('outputs', spec_type=type_)


def spec_testoutput_ids(spec):
        return spec.get('outputs', {}).keys()

def spec_unused_testoutput_ids(spec):
    out_ids = set(spec_testoutput_ids(spec))
    for ev in spec.get('evaluations', []):
        for eis in ev.get('inputs', {}):
            if not isinstance(eis, dict):
                eis = ev['inputs'].get(eis, {})
            # now eis is always a dict
            if eis.get('origin', None) == 'testoutput':
                out_ids = out_ids.difference(set([eis['value']]))
    return list(out_ids)


