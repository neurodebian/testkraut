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

def VolumeRMSD(ref, samp):
    """Root mean squared deviation"""
    import numpy as np
    import nibabel as nb
    d = nb.load(ref).get_data()
    samp = nb.load(samp).get_data()
    d -= samp
    rmsd = np.sqrt(np.sum(np.square(d)) / np.prod(d.shape))
    return rmsd

