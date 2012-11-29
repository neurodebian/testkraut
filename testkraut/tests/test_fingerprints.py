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

from testkraut.fingerprinting import *
from nose.tools import *
from .utils import with_tempdir
from os.path import join as opj
import numpy as np

def test_fingerprint_dict():
    vol_fp = get_fingerprinters('volumetric image')
    assert_true(len(vol_fp))

@with_tempdir()
def test_numeric_values_fp(wdir):
    stuff="""/NumWaves	4
/NumPoints	180
/PPheights		1.000000e+00	7.177207e-01	1.000000e+00	7.177133e-01

/Matrix
8.868212e-02	3.147391e-02	-6.863332e-02	3.371175e-02	
1.183776e-01	3.039748e-02	-3.464294e-02	3.336017e-02	
"""
    fname = opj(wdir, 'numeric')
    f=open(fname, 'w')
    f.write(stuff)
    f.close()
    fp = {}
    # should auto-detect the comment character '/'
    fp_numeric_values(fname, fp, ['text file', 'columns', 'rows'])
    assert_equal(fp['shape'], (2, 4))
    assert_equal(len(fp['column_mean']), 4)
    assert_equal(len(fp['row_std']), 2)
    assert_equal(len(fp['row_pwr_spectr']), 2)

@with_tempdir()
def test_table_fp(wdir):
    ttable="""Cluster Index\tVoxels\tP\t-log10(P)\tZ-MAX\tZ-MAX X (vox)\tZ-MAX Y (vox)\tZ-MAX Z (vox)\tZ-COG X (vox)\tZ-COG Y (vox)\tZ-COG Z (vox)	
a\t4134\t0\t149\t17.4\t46\t28\t8\t33.1\t23.6\t9.18
b\t35\t0.000126\t3.9\t4.53\t37\t34\t17\t37.4\t34.3\t16.7

"""
    table_name = opj(wdir, 'texttable')
    f=open(table_name, 'w')
    f.write(ttable)
    f.close()
    fp = {}
    fp_table(table_name, fp, ['text file'])
    assert_equal(len(fp), 12) # one for __version__
    assert_equal(type(fp['Cluster Index'][0]), str)
    assert_true(np.issubdtype(type(fp['Voxels'][1]), int))
    assert_true(np.issubdtype(type(fp['P'][1]), float))
    # but also
    assert_true(np.issubdtype(type(fp['P'][0]), float))
