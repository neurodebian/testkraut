.. -*- mode: rst; fill-column: 78; indent-tabs-mode: nil -*-
.. vi: set ft=rst sts=4 ts=4 sw=4 et tw=79:
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
  #
  #   See COPYING file distributed along with the testkraut package for the
  #   copyright and license terms.
  #
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

.. _chap_output_fingerprinting:

*********************
Output fingerprinting
*********************

.. currentmodule:: testkraut

Modules with fingerprint generators:

.. autosummary::
   :toctree: generated

   fingerprints
   fingerprints.base


Writing a custom fingerprinting function
========================================

Writing a custom fingerprint implementation for a particular kind of output
is pretty straightforward. Start by creating a function with the following
interface::

  def fp_my_fingerprint(fname, fpinfo, tags):
    pass

The variable ``fname`` will contain the filename/path of the output for which a
fingerprint shall be created. ``fpinfo`` is an empty dictionary to which the
content of the fingerprint needs to be added. A test runner will add this
dictionary to the ``fingerprints`` section of the respective output file in the
SPEC. The name of the fingerprinting function itself will be used as key for
this fingerprint element in that section. Any ``fp_``-prefix, as in the example
above, will be stripped from the name. Finally, ``tags`` is a sequence of
:ref:`chap_output_tags` that categorize a file and can be used to adjust the
content of a fingerprint accordingly.

Any fingerprinting function must add a ``__version__`` tag to the fingerprint.
The version must be incremented whenever the fingerprint implementation
changes, to make longitudinal comparisons of test results more accurate.

There is no need to return any value -- all content needs to be added to the
``fpinfo`` dictionary.

A complete implementation of a fingerprinting function that stores the size of
an input file could look like this::

  >>> import os
  >>> def fp_file_size(fname, fpinfo, tags):
  ...   fpinfo['__version__'] = 0
  ...   fpinfo['size'] = os.path.getsize(fname)
  >>> #
  >>> # test it
  >>> #
  >>> from testkraut.fingerprints import proc_fingerprint
  >>> fingerprints = {}
  >>> proc_fingerprint(fp_file_size, fingerprints, 'COPYING')
  >>> 'file_size' in fingerprints
  True
  >>> 'size' in fingerprints['file_size']
  True

There is no need to catch exceptions inside fingerprinting functions. The test
runner will catch any exception and everything that has been stored in the
fingerprint content dictionary up to when the exception occurred will be
preserved. The exception itself will be logged in a ``__exception__`` field.

To enable the new fingerprinting function, add it to any appropriate tag in the
``fingerprints`` section of the configuration file::

  [fingerprints]
  want size = myownpackage.somemodule.fp_file_size

With this configuration this fingerprint will be generated for any output that
is tagged ``want size``. It is required that the function is "importable" from
the specified location.
