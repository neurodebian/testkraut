# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Generic fingerprint generators for a wide range of file types"""

__docformat__ = 'restructuredtext'

import os
import operator
import logging
import fileinput
lgr = logging.getLogger(__name__)

def fp_file(fname, fp, tags):
    """Basic fingerprint for any file

    The fingerprint contains the size of the file on disk, as reported by
    os.stat (field ``size``). If ``libmagic`` is installed, the fingerprint
    will also contain a label for the file type as guessed by libmagic
    (identical to what would have been returned by the ``file`` command).
    """
    fp['__version__'] = 0
    fp['size'] = os.path.getsize(fname)
    try:
        from ..external import magic
        fp['magic'] = magic.from_file(fname)
    except ImportError:
        lgr.debug("no 'magic' package found -- cannot determine filemagic")

def fp_volume_image(fname, fp, tags):
    """Fingerprint for volumetric images
    """
    # this version needs an increment whenever this implementation changes
    fp['__version__'] = 0
    import nibabel as nb
    import numpy as np
    from scipy.ndimage import measurements as msr
    from scipy.stats import describe
    img = nb.load(fname)
    img_data = img.get_data().astype('float') # float for z-score
    # cleanup the original image to get a leaner footprint
    del img
    # keep a map where the original data is larger than zero
    zero_thresh = img_data > 0
    # basic descriptive stats
    img_size, img_minmax, img_mean, img_var, img_skew, img_kurt = \
            describe(img_data, axis=None)
    img_std = np.sqrt(img_var)
    fp['std'] = img_std
    fp['mean'] = img_mean
    fp['min'] = img_minmax[0]
    fp['max'] = img_minmax[1]
    fp['skewness'] = img_skew
    fp['kurtosis'] = img_kurt
    if not 'zscores' in tags and not 'tscores' in tags:
        # unknown distribution of values -> global zscore to normalize
        img_data -= img_mean
        img_data /= img_std
    zmin = img_data.min()
    zmax = img_data.max()
    # normalized luminance histogram
    luminance_hist_params = (-10, 10, 21)
    fp['histogram_[%i,%i,%i]' % luminance_hist_params] = \
            np.histogram(img_data, normed=True,
                         bins=np.linspace(*luminance_hist_params))[0]
    if not img_std:
        # no variance, nothing to do
        return
    if not '3D image' in tags:
        # the following clustering can become insane for 4D and higher images
        return
    # perform thresholding at various levels and compute descriptive
    # stats of the resulting clusters
    clusters = np.empty(img_data.shape, dtype=np.int32)
    for thresh in (zero_thresh, 2.0, 4.0, 8.0, -2.0, -4.0, -8.0):
        # create a binarized map for the respective threshold
        if not isinstance(thresh, float):
            thresh_map = thresh
            thresh = 'orig_zero'
        else:
            if thresh < 0:
                if thresh < zmin:
                    # thresholding would yield nothing
                    continue
                thresh_map = img_data < thresh
            else:
                if thresh > zmax:
                    # thresholding would yield nothing
                    continue
                thresh_map = img_data > thresh
        nclusters = msr.label(thresh_map, output=clusters)
        # sort by cluster size
        cluster_sizes = [(cl, np.sum(clusters == cl))
                                for cl in xrange(1, nclusters + 1)]
        cluster_sizes = sorted(cluster_sizes,
                               key=operator.itemgetter(1),
                               reverse=True)
        # how many clusters to report
        max_nclusters = 3
        if not len(cluster_sizes):
            # nothing to report, do not clutter the dict
            continue
        clinfo = {}
        fp['thresh_%s' % thresh] = clinfo
        clinfo['nclusters'] = nclusters
        # only for the biggest clusters
        cl_id = 0
        for cl_label, cl_size in cluster_sizes[:max_nclusters]:
            cl_id += 1
            cli = dict(size=cl_size)
            clinfo['cluster_%i' % cl_id] = cli
            # center of mass of the cluster extent (ignoring actual values)
            cli['extent_ctr_of_mass'] = \
                    msr.center_of_mass(thresh_map, labels=clusters,
                                       index=cl_label)
            # center of mass of the cluster considering actual values
            cli['ctr_of_mass'] = msr.center_of_mass(img_data,
                                                    labels=clusters,
                                                    index=cl_label)
            if isinstance(thresh, float) and thresh < 0:
                # position of minima
                pos = msr.minimum_position(img_data, labels=clusters, index=cl_label)
                cli['min_pos'] = pos
                cli['min'] = img_data[pos]
            else:
                # position of maxima
                pos = msr.maximum_position(img_data, labels=clusters, index=cl_label)
                cli['max_pos'] = pos
                cli['max'] = img_data[pos]

def fp_nifti1_header(fname, fp, tags):
    """Store the content of a NIfTI1 file header as fingerprint.

    The fingerprint will also contain type codes and sizes for any header
    extension found in a file.
    """
    import nibabel as nb
    import numpy as np
    img = nb.load(fname)
    fp['__version__'] = 0
    hdr = img.get_header()
    for k, v in hdr.items():
        if not len(v.shape):
            # 0d fellas
            fp[k] = v.item()
        elif np.issubdtype(v.dtype, float):
            fp[k] = [float(i) for i in v]
        elif np.issubdtype(v.dtype, int):
            fp[k] = [int(i) for i in v]
        else:
            fp[k] = unicode(v)
    fp['extension_codes'] = hdr.extensions.get_codes()
    fp['extension_sizes'] = [e.get_sizeondisk() for e in hdr.extensions]

def fp_numeric_values(fname, fp, tags):
    """Basic fingerprint for matrices are arrays of numeric values.

    For text files this function is trying to determine a potential comment
    character before reading the file content is handed over to NumPy's
    ``loadtxt()`` function.

    Any data array will be described with basic statistics (mean, std, ...),
    size of the matrix and data type. Files tagged 'columns' or 'rows' will
    get per column or per row statistics respectively. Additionally, the
    fingerprint for such files will also contain the average power spectrum.
    """
    fp['__version__'] = 0
    import numpy as np
    if 'text file' in tags:
        first_chars = set()
        fi = fileinput.FileInput(fname, openhook=fileinput.hook_compressed)
        for line in fi:
            first_chars.add(line[0])
        comment_char = first_chars.difference(
                [str(i) for i in range(10)] + ['\n', '\t', ' ', '.', '-'])
        if len(comment_char) > 1:
            raise ValueError("Cannot determine the comment character")
        if len(comment_char):
            comment_char = comment_char.pop()
        else:
            comment_char = None
        if 'whitespace-separated fields' in tags:
            delimiter=None
        else:
            delimiter=None
        data = np.loadtxt(fname, comments=comment_char)
    else:
        # TODO load binary data
        return
    # basic info
    fp['dtype'] = data.dtype.name
    if len(data.shape):
        fp['shape'] = data.shape
    else:
        fp['value'] = data.item()
        # we cannot be more precise
        return
    from scipy.stats import describe
    # what is the interesting axis
    did_something = False
    # a bit complicated to allow for description of rows and columns
    for tag, axis in (('column', 0), ('row', 1)):
        if not '%ss' % tag in tags:
            if did_something:
                continue
            else:
                # do stats on the whole thing
                axis = None
                tag = 'global'
        did_something = True
        # basic descriptive stats
        _size, _minmax, _mean, _var, _skew, _kurt = describe(data, axis=axis)
        fp['%s_std' % tag] = np.sqrt(_var)
        fp['%s_mean' % tag] = _mean
        fp['%s_min' % tag] = _minmax[0]
        fp['%s_max' % tag] = _minmax[1]
        fp['%s_skewness' % tag] = _skew
        fp['%s_kurtosis' % tag] = _kurt
        if not axis is None:
            fp['%s_pwr_spectr' % tag] = \
                    np.mean(np.abs(np.fft.fft(data, axis=axis))**2, axis=axis)


def fp_table(fname, fp, tags):
    """Read an entire table instead of computing a actual fingerprint

    For text files, any table format dialect that is understood but the 'csv'
    module can be read in full. Tables have to have a header with column names.
    These names are used as fieldnames in the fingerprint structure. The actual
    column data is stored in full. However, an attempt is made to determine the
    dtype of each column individually and convert the data accordingly. Only
    integer values, floating point numbers and strings are distinguished.
    """
    fp['__version__'] = 0
    if 'text file' in tags:
        _fp_text_table(fname, fp, tags)

def _fp_text_table(fname, fp, tags):
    import csv
    f = open(fname, 'rU')
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(f.read(1024))
    except:
        # maybe a sloppy header with a trailing delimiter?
        f.seek(0)
        sample = [f.readline() for s in range(3)]
        sample[0] = sample[0].strip()
        dialect = sniffer.sniff('\n'.join(sample))
    f.seek(0)
    reader = csv.DictReader(f, dialect=dialect)
    fp.update(dict(zip(reader.fieldnames,
                       [list() for i in xrange(len(reader.fieldnames))])))
    for row in reader:
        for k, v in row.iteritems():
            fp[k].append(v)
    # improve dtypes -- do last do keep data when no numpy is around
    import numpy as np
    del_me = []
    for k, v in fp.iteritems():
        if k.startswith('__') and k.endswith('__'):
            continue
        if not len(k) and len(v) and v[0] is None:
            # this is an artifact of a trailing delimiter
            del_me.append(k)
        try:
            fp[k] = np.array(v, dtype=int)
        except ValueError:
            try:
                fp[k] = np.array(v, dtype=float)
            except ValueError:
                # we tried ...
                pass
        except TypeError:
            # tolerate any unexpected types and keep them as is
            pass
    for d in del_me:
        # delete artifacts
        del fp[d]
