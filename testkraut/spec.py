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

__allowed_spec_keys__ = [
        'test',
        'depends',
        'description',
        'id',
        'input spec',
        'output spec',
        'version',
        'evaluation',
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


class SPEC(dict):
    def __init__(self, src=None):
        dict.__init__(self)
        if isinstance(src, file):
            self.update(json.load(src))
        elif isinstance(src, basestring):
            self.update(json.loads(src))
        self._check()

    def _check(self):
        _verify_tags(self, ('id', 'version'), 'SPEC')
        for i, ev in enumerate(self.get('evaluation', [])):
            _verify_tags(ev, ('id', 'input spec', 'operator'),
                         'evaluation %i' % i)
        _verify_spec_tags(self.get('output spec', {}), ('type', 'value'),
                          'output spec')
        _verify_spec_tags(self.get('input spec', {}), ('type', 'value'),
                          'input spec')

    def __setitem__(self, key, value):
        if not key in __allowed_spec_keys__:
            _raise(ValueError, "refuse to add unsupported key", key)
        if key == 'version':
            if not isinstance(value, int) or value < 0:
                _raise(ValueError,
                    "version needs to be a non-negative integer value "
                    "(got: %s)." % value)
        dict.__setitem__(self, key, value)

def spec_testoutput_ids(spec):
        return spec.get('output spec', {}).keys()

def spec_unused_testoutput_ids(spec):
    out_ids = set(spec_testoutput_ids(spec))
    for ev in spec.get('evaluation', []):
        for eis in ev.get('input spec', {}):
            if not isinstance(eis, dict):
                eis = ev['input spec'].get(eis, {})
            # now eis is always a dict
            if eis.get('origin', None) == 'testoutput':
                out_ids = out_ids.difference(set([eis['value']]))
    return list(out_ids)


