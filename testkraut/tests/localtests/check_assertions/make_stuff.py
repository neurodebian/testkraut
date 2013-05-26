import nibabel as nb
import numpy as np

data = np.random.standard_normal((16,16,8))
data *= 1000
nb.Nifti1Image(data, np.eye(4)).to_filename('orig.nii.gz')
for i in range(1, 3):
    nb.Nifti1Image(
        data + (np.random.standard_normal(data.shape) * i), 
        np.eye(4)).to_filename('noise_%i.nii.gz' % i)
