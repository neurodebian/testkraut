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

__allowed_spec_keys__ = \
        ['command',
         'depends',
         'description',
         'id'
         'input spec',
         'output spec',
         'version'
        ]

class SPEC(dict):
    def __init__(self, src=None):
        dict.__init__(self)
        if isinstance(src, file):
            self.update(json.load(src))
        elif isinstance(src, basestring):
            self.update(json.loads(src))
        self._check()

    def _check(self):
        # mandatory ID
        if not 'id' in self:
            self._raise(ValueError, 'Mandatory ID not specified')
        # assign defaults
        for k, v in (('command', None),
                     ('depends', list()),
                     ('description', ''),
                     ('input spec', dict()),
                     ('output spec', dict()),
                     ('version', 0)):
            if not k in self:
                self[k] = v

    def __setitem__(self, key, value):
        if not key in __allowed_spec_keys__:
            self._raise(ValueError, "Refuse to add unsupported key", key)
        if key == 'version':
            if not isinstance(value, int) or value < 0:
                self._raise(ValueError,
                    "version needs to be a non-negative integer value "
                    "(got: %s)." % value)
        dict.__setitem__(self, key, value)

    def _raise(self, exception, why, input=None):
        if not input is None:
            input = ' (got: %s)' % repr(input)
        else:
            input = ''
        raise exception("SPEC: %s%s" % (why, input))

