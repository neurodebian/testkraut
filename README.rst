testkraut -- hopefully not yet another software testing framework
=================================================================

  *Note: testkraut is still in its infancy -- some of what is written here
  could still be an anticipation of the near future.*

Anyway, this is nevertheless a framework for software testing. That being said,
testkraut tries to minimize the overlap with the scopes of unit testing,
regression testing, and continuous integration testing. Instead, it aims to
complement these kinds of testing, and is able to re-use them, or can be
integrated with them.

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

More documentation:
  https://testkraut.readthedocs.org

Build status:
  http://travis-ci.org/neurodebian/testkraut


Prototypes of a testkraut user
------------------------------

The concerned scientist
~~~~~~~~~~~~~~~~~~~~~~~

This scientist came up with a sophisticated data analysis pipeline, consisting
of many pieces of software from different vendors. It appears to work correctly
(for now). But this scientist is afraid to upgrade any software on the machine,
because it might break the pipeline. Rigorous tests would have helped, but
"there was no time". testkraut can help to (semi-automatically) assess the
longitudinal stability of analysis results.

The thoughtful software developer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For any individual software developer or project it is almost impossible to
confirm proper functioning of their software on all possible computing
environments. testkraut can help generate informative performance reports that
can be send back to a developer and offer a more comprehensive assessment
of cross-platform performance.

The careful "downstream"
~~~~~~~~~~~~~~~~~~~~~~~~

A packager for a software distribution needs to apply a patch to some software
to improve its integration into the distribution environment. Of course, such a
patch should not have a negative impact on the behavior of the software.
testkraut can help to make a comparative assessment to alert the packager if
something starts to behave in unexpected ways.

Wanna help?
-----------

If you think it would be worthwhile to contribute to this project your
input would be highly appreciated. Please report issues, send feature-requests,
and pull-request without hesitation!

Why this name?
--------------

The original aim for this project was to achieve "crowd-sourcing" of software
testing efforts. "kraut" is obviously almost a semi-homonym of "crowd", while
at the same time indicating that this software spent its infancy at the
Institute of Psychology Magdeburg, Germany.

License
-------

All code is licensed under the terms of the MIT license, or some equally liberal
alternative license. Please see the COPYING file in the source distribution for
more detailed information.
