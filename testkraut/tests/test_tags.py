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

afni_1D="""\
# <matrix
#  ni_type = "9*double"
#  ni_dimen = "2"
#  ColumnLabels = "Run#1Pol#0 ; Run#1Pol#1 ; Run#1Pol#2 ; Run#1Pol#3 ; Run#1Pol#4 ; Stim#1#0 ; Stim#1#1 ; Stim#2#0 ; Stim#2#1"
#  ColumnGroups = "5@-1,2@1,2@2"
#  RowTR = "3"
#  GoodList = "0..1"
#  NRowFull = "2"
#  RunStart = "0"
#  Nstim = "2"
#  StimBots = "5,7"
#  StimTops = "6,8"
#  StimLabels = "Stim#1 ; Stim#2"
#  BasisNstim = "2"
#  BasisOption_000001 = "-stim_times"
#  BasisName_000001 = "Stim#1"
#  BasisFormula_000001 = "SPMG2(30)"
#  BasisColumns_000001 = "5:6"
#  BasisOption_000002 = "-stim_times"
#  BasisName_000002 = "Stim#2"
#  BasisFormula_000002 = "SPMG2(45)"
#  BasisColumns_000002 = "7:8"
#  CommandLine = "3dDeconvolve some more stuff"
# >
 1 -0.99999999867545 0.99441340146586 -0.99999999536408 0.99434100370854 0 0 0 0
 1 -0.98882681431791 0.96108110846627 -0.93389370243179 0.88539371934775 0.088518142700195 0.57121348381042 0.088518142700195 0.57121855020523
"""

@with_tempdir()
def test_guess_tags(wdir):
    contents = (
        (text_array, 'test.txt',
         ('numeric values', 'text file', 'whitespace-separated fields',
          'table', 'columns')),
        (csv_table, 'test.csv',
         ('table', 'text file',)),
        (afni_1D, 'test.1D',
         ('afni 1d', 'text file', 'numeric values', 'columns',
          'whitespace-separated fields', 'rows', 'table')),
    )
    for content, fname, tags in contents:
        fname = opj(wdir, fname)
        f=open(fname, 'w')
        f.write(content)
        f.close()
        assert_equal(guess_file_tags(fname), set(tags))
