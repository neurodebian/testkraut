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

import sys

# stupid dummy for now
def debug(channel, msg):
    print channel, msg

# stupid dummy for now
def verbose(level, msg):
    print msg

# stupid dummy for now
def error(msg):
    print msg
    sys.exit(1)

