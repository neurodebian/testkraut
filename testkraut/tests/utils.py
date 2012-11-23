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

from nose.tools import *

def with_tempdir(*targs, **tkwargs):
    def decorate(func):
        def newfunc(*arg, **kwargs):
            import tempfile
            wdir = tempfile.mkdtemp(*targs, **tkwargs)
            try:
                func(*((wdir,) + arg), **kwargs)
            finally:
                import shutil
                shutil.rmtree(wdir)
        newfunc = make_decorator(func)(newfunc)
        return newfunc
    return decorate
