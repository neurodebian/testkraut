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

 columns
   columns of a matrix or an array should be described individually

 nifti1 format
   a file in any variant of the NIfTI1 format

 numeric values
   a file containing an array/matrix of numeric values

 rows
   rows of a matrix or an array should be described individually

 text file
   a file with text-only, i.e. non-binary content

 table
   a file with data table layout (if a text format, column names are in first
   line; uniform but arbitrary delimiter)

 tscores
   values from a `Student’s t-distribution
   <http://en.wikipedia.org/wiki/Student%E2%80%99s_t-distribution>`_

 volumetric image
   a multi-dimensional (three or more) image

 whitespace-separated fields
   data in a structured text format where individual fields are separated by any
   white-space character(s)

 zscores
   standardized values indicating how many standard deviations an original
   value is above or below the mean
