**********************************************
Not another software testing framework, please
**********************************************

  *Note: testkraut is still in its infancy -- some of what is written here
  could still be an anticipation of the near future.*

This is a framework for software testing. That being said, testkraut tries to
minimize the overlap with the scopes of unit testing, regression testing, and
continuous integration testing. Instead, it aims to complement these kinds of
testing, and is able to re-use them, or can be integrated with them.

In a nutshell testkraut helps to facilitate statistical analysis of test
results. In particular, it focuses on two main scenarios:

1. Comparing results of a single (test) implementation across different
   or changing computational environments (think: different operating systems,
   different hardware, or the same machine before an after a software upgrade).

2. Comparing results of different (test) implementations generating similar
   output from identical input (think: performance of various signal detection
   algorithms).

While such things can be done using other available tools as well, testkraut
aims to provide a lightweight (hence portable), yet comprehensive description
of a test run. Such a description allows for decoupling test result generation
and analysis -- opening up the opportunity to "crowd-source" software testing
efforts, and aggregate results beyond the scope of a single project, lab,
company, or site.

.. link list

`Bug tracker <https://github.com/neurodebian/testkraut/issues>`_ |
`Build status <http://travis-ci.org/neurodebian/testkraut>`_ |
`Documentation <https://testkraut.readthedocs.org>`_ |
`Downloads <https://github.com/neurodebian/testkraut/tags>`_ |
`PyPi <http://pypi.python.org/pypi/testkraut>`_
