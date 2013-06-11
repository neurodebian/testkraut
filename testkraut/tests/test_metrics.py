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
from .. import metrics as mtrc
from .utils import with_tempdir
from os.path import join as opj
import numpy as np

@with_tempdir()
def test_volumermsd(wdir):
    # make sample timeseries
    import nibabel as nb
    data = np.random.randn(16, 16, 8, 4)
    data_fname = opj(wdir, 'data.nii.gz')
    ref_fname = opj(wdir, 'refvol.nii.gz')
    first_fname = opj(wdir, 'firstvol.nii.gz')
    refvol = 2
    nb.Nifti1Image(data, np.eye(4)).to_filename(data_fname)
    nb.Nifti1Image(data[..., refvol], np.eye(4)).to_filename(ref_fname)
    nb.Nifti1Image(data[..., 0], np.eye(4)).to_filename(first_fname)
    rmsd_vol = mtrc.VolumeRMSD(data_fname, refvol)
    rmsd_file = mtrc.VolumeRMSD(data_fname, ref_fname)
    rmsd_3d = mtrc.VolumeRMSD(first_fname, ref_fname)
    assert_sequence_equal(rmsd_vol, rmsd_file)
    assert_equal(rmsd_3d, rmsd_vol[0])
