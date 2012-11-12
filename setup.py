# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""""""

import os
import sys
from os.path import join as opj
import testkraut
from distutils.core import setup
from glob import glob


__docformat__ = 'restructuredtext'

extra_setuptools_args = {}
if 'setuptools' in sys.modules:
    extra_setuptools_args = dict(
        tests_require=['nose'],
        test_suite='nose.collector',
        zip_safe=False,
        extras_require = dict(
            doc='Sphinx>=0.3',
            test='nose>=0.10.1')
    )

def main(**extra_args):
    setup(name         = 'testkraut',
          version      = testkraut.__version__,
          author       = 'Michael Hanke and the testkraut developers',
          author_email = 'michael.hanke@gmail.com',
          license      = 'MIT License',
          url          = 'https://github.com/neurodebian/testkraut',
          description  = 'test and evaluate heterogeneous data processing pipelines',
          long_description = "",
          # please maintain alphanumeric order
          packages     = [ 'testkraut',
                           'testkraut.cmdline',
                           'testkraut.evaluators',
                           'testkraut.external',
                           'testkraut.tests',
                           ],
          data_files = [(opj('share', 'testkraut', test), [f for f in glob(opj(test, '*'))
                                    if os.path.isfile(f)])
                            for test in glob(opj('library', '*')) if os.path.isdir(test)],
          scripts      = glob(os.path.join('bin', '*'))
          )

if __name__ == "__main__":
    main(**extra_setuptools_args)
