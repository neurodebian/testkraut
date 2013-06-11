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

def VolumeRMSD(samp, ref):
    """Root mean squared deviation of sample from reference volume

    Parameters
    ----------
    samp : filename
      Sample image (3d/4d).
    ref: int or filename
      If an integer, the corresponding volume from the sample timeseries is
      used as a reference. Otherwise the respective file with a 3D image
      is loaded.

    Returns
    -------
    list or float
      With a 3D sample image a single float is returned, a list of floats
      otherwise.
    """
    import numpy as np
    import nibabel as nb
    samp = nb.load(samp).get_data()
    threed = len(samp.shape) == 3
    if isinstance(ref, int):
        ref = samp[..., ref]
    else:
        ref = nb.load(ref).get_data()
    if len(samp.shape) < 4:
        samp = samp[...,None]
    rmsd = [np.sqrt(np.sum(np.square(d - ref)) / np.prod(d.shape))
                for d in np.rollaxis(samp, 3,0)]
    if threed:
        return rmsd[0]
    else:
        return rmsd

