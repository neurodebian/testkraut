
def image_nelements_positive(filepath):
    import nibabel as nb
    import numpy as np
    img = nb.load(filepath)
    return np.sum(img.get_data() > 0)
