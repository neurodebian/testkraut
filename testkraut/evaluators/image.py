import nibabel as nb
import numpy as np

def image_nelements_positive(filepath):
    img = nb.load(filepath)
    return np.sum(img.get_data() > 0)
