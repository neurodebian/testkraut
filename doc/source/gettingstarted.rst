.. -*- mode: rst; fill-column: 78; indent-tabs-mode: nil -*-
.. vi: set ft=rst sts=4 ts=4 sw=4 et tw=79:
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
  #
  #   See COPYING file distributed along with the testkraut package for the
  #   copyright and license terms.
  #
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

.. _chap_getting_started:

*********************
Get started (quickly)
*********************

This should not take much time. testkraut contains no compiled code. It should
run with Python 2.6 (or later) -- although Python 3x hasn't been tested (yet).
If you are running Python 2.6 you should install the argparse_ package,
otherwise you won't have much fun. Here is a list of things the make life
more interesting:

NumPy_
   not strictly required, but strongly recommended. There should be no need
   to have any particular version.

SciPy_
   will improve the test result reporting -- any reasonably recent version
   should do

libmagic_
   helps to provide more meaningful information on file types

python-colorama_
   for more beautiful console output -- but monochrome beings don't need it

.. _argparse: http://pypi.python.org/pypi/argparse
.. _NumPy: http://numpy.scipy.org
.. _SciPy: http://www.scipy.org
.. _libmagic: http://www.darwinsys.com/file
.. _python-colorama: http://pypi.python.org/pypi/colorama


Download ...
============

testkraut is available from PyPi_, hence it can be installed with
``easy_install`` or ``pip`` -- the usual way. ``pip`` seems to be a little saner
than the other one, so we'll use this::

  % pip install testkraut

This should download and install the latest version. Depending on where you are
installing you might want to call ``sudo`` for additional force.

``pip`` will tell you where it installed the main ``testkraut`` script.
Depending on your setup you may want to add this location to your ``PATH``
environment variable.

.. _PyPi: http://pypi.python.org

... and run
===========

.. _FSL: http://www.fmrib.ox.ac.uk/fsl

Now we're ready to run our first test. The ``demo`` test requires FSL_ to be
installed and configured to run (properly set ``FSLDIR`` variable and so on...).
The main testkraut script supports a number of commands that are used to prepare
and run tests. A comprehensive listing is available form the help output::

  % testkraut --help

To run the ``demo`` test, we need to obtain the required test data first. This
is done by telling testkraut to cache all required files locally::

  % testkraut cachefiles demo

It will download an anatomical image from a webserver. However, since the image
is the MNI152 template head that comes with FSL, you can also use an existing
local file to populate the cache -- please explore the options for this
command.

Now we are ready to run::

  % testkraut execute demo

If FSL is functional, this command will run a few seconds and create a
subdirectory ``testbeds/demo`` with the test in/output and a comprehensive
description of the test run in JSON format::

  % ls testbeds/demo
  brain_mask.nii.gz  brain.nii.gz  head.nii.gz  spec.json

That is it -- for now...

