.. -*- mode: rst; fill-column: 78; indent-tabs-mode: nil -*-
.. vi: set ft=rst sts=4 ts=4 sw=4 et tw=79:
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
  #
  #   See COPYING file distributed along with the testkraut package for the
  #   copyright and license terms.
  #
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

.. _chap_output_tags:

***********
Output tags
***********

This glossary lists all known tags that can be used to label test outputs.
According to the assigned tags appropriate fingerprinting or evaluation
methods are automatically applied to the output data.

.. glossary::

 3D image, 4D image
   a sub-category of :term:`volumetric image` with a particular number of axes

 nifti1 format
   a file in any variant of the NIfTI1 format

 space-separated values
   data in text format where individual numeric values are separated by any
   white-space character(s)

 text file
   a file with text-only, i.e. non-binary content

 tscores
   values from a `Student’s t-distribution
   <http://en.wikipedia.org/wiki/Student%E2%80%99s_t-distribution>`_

 volumetric image
   a multi-dimensional (three or more) image

 zscores
   standardized values indicating how many standard deviations an original
   value is above or below the mean
