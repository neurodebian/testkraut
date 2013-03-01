# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Unittest compliant API for testkraut test cases"""

__docformat__ = 'restructuredtext'

import os
from os.path import join as opj
import json
from functools import wraps

import logging
lgr = logging.getLogger(__name__)

from testtools import TestCase, RunTest
from testtools.content import Content
from testtools.content_type import ContentType

from .utils import get_test_library_paths
from .spec import SPEC, SPECJSONEncoder

console = logging.StreamHandler()
lgr.addHandler(console)
lgr.setLevel(logging.DEBUG)

#
# Utility code for template-based test cases
#
def TestArgs(*args, **kwargs):
    """Little helper to specify test arguments"""
    return (args, kwargs)

def test_template(args):
    def wrapper(func):
        func.template = args
        return func
    return wrapper

def _method_partial(func, *parameters, **kparms):
    @wraps(func)
    def wrapped(self, *args, **kw):
        kw.update(kparms)
        return func(self, *(args + parameters), **kw)
    return wrapped

class TemplateTestCase(type):
    """
    Originally based on code from
    https://bitbucket.org/lothiraldan/unittest-templates

    Copyright 2011, Boris Feld <http://boris.feld.crealio.fr>
    License: DTFYWTPL
    """
    #            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
    #                Version 2, December 2004
    #
    # Copyright (C) 2004 Sam Hocevar <sam@hocevar.net>
    #
    # Everyone is permitted to copy and distribute verbatim or modified
    # copies of this license document, and changing it is allowed as long
    # as the name is changed.
    #
    #            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
    #   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
    #
    #  0. You just DO WHAT THE FUCK YOU WANT TO.
    def __new__(cls, name, bases, attr):
        new_methods = {}
        for method_name in attr:
            if hasattr(attr[method_name], "template"):
                source = attr[method_name]
                source_name = method_name.lstrip("_")
                for test_name, args in source.template.items():
                    parg, kwargs = args
                    new_name = "test_%s" % test_name
                    new_methods[new_name] = _method_partial(source, *parg, **kwargs)
                    new_methods[new_name].__name__ = str(new_name)
        attr.update(new_methods)
        return type(name, bases, attr)

def discover_specs():
    """Helper function to discover test SPECs in configured library locations
    """
    discovered = {}
    # for all configured test library locations
    for tld in get_test_library_paths():
        # for all subdirs
        for subdir in [d for d in os.listdir(tld)
                            if os.path.isdir(opj(tld, d))]:
            spec_fname = opj(tld, subdir, 'spec.json')
            if not os.path.isfile(spec_fname):
                # not a test spec
                lgr.debug("ignoring '%s' directory in library path '%s': contains no SPEC file"
                          % (subdir, tld))
                continue
            try:
                spec = SPEC(open(spec_fname))
                spec_id = spec['id'].replace('-', '_')
            except:
                # not a valid SPEC
                lgr.warning("ignoring '%s': no a valid SPEC file"
                          % spec_fname)
            if spec_id in discovered:
                lgr.warning("found duplicate test ID '%s' in %s: ignoring the latter test"
                            % (spec_id, (discovered[spec_id], spec_fname)))
                continue
            # we actually found a new one
            lgr.debug("discovered test SPEC '%s'" % spec_id)
            discovered[spec_id] = spec_fname
    # wrap spec file locations in TestArgs
    return dict([(k, TestArgs(v)) for k, v in discovered.iteritems()])


class TestFromSPEC(TestCase):
    __metaclass__ = TemplateTestCase

    @test_template(discover_specs())
    def _run_spec_test(self, spec_filename):
        spec = SPEC(open(spec_filename))
        spec_id = spec['id']
        print spec_id
        self.assertEqual(49, 49)
        #self.addDetail('input spec',
        #               Content(ContentType('application', 'json'),
        #                       lambda: [json.dumps(spec['inputs'],
        #                                           cls=SPECJSONEncoder)])
        #              )

    def setUp(self):
        """Runs prior each test run"""
        super(TestFromSPEC, self).setUp()
        #self._wdir = 'bla'

    def tearDown(self):
        """Runs after each test run"""
        super(TestFromSPEC, self).tearDown()
        #self._wdir = None


