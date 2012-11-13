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

from testkraut.config import ConfigManager
from nose.tools import *

def test_config():
    cfg = ConfigManager()
    # for now just running it a bit

    # query for some non-existing option and check if default is returned
    query = cfg.get('dasgibtsdochnicht', 'neegarnicht', default='required')
    assert_equal(query, 'required')

