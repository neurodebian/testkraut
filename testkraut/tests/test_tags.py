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

from ..utils import guess_file_tags
from nose.tools import *
from .utils import with_tempdir
from os.path import join as opj

text_array="""\
1 0.3
2 0.32
3 4309.3
"""

csv_table="""\
somea, someb, somec
ab, 3, 3.4
cd, 4, .45
de, 5, -2.566
"""

@with_tempdir()
def test_guess_tags(wdir):
    contents = (
        (text_array,
         ('numeric values', 'text file', 'whitespace-separated fields',
          'table', 'columns')),
        (csv_table,
         ('table', 'text file',)),
    )
    for content, tags in contents:
        fname = opj(wdir, 'testfile')
        f=open(fname, 'w')
        f.write(content)
        f.close()
        assert_equal(guess_file_tags(fname), set(tags))
