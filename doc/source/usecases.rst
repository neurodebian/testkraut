.. -*- mode: rst; fill-column: 78; indent-tabs-mode: nil -*-
.. vi: set ft=rst sts=4 ts=4 sw=4 et tw=79:
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
  #
  #   See COPYING file distributed along with the testkraut package for the
  #   copyright and license terms.
  #
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

.. _chap_usecases:

******************************
Prototypes of a testkraut user
******************************

The concerned scientist
=======================

This scientist came up with a sophisticated data analysis pipeline, consisting
of many pieces of software from different vendors. It appears to work correctly
(for now). But this scientist is afraid to upgrade any software on the machine,
because it might break the pipeline. Rigorous tests would have helped, but
"there was no time". testkraut can help to (semi-automatically) assess the
longitudinal stability of analysis results.

The thoughtful software developer
=================================

For any individual software developer or project it is almost impossible to
confirm proper functioning of their software on all possible computing
environments. testkraut can help generate informative performance reports that
can be send back to a developer and offer a more comprehensive assessment
of cross-platform performance.

The careful "downstream"
========================

A packager for a software distribution needs to apply a patch to some software
to improve its integration into the distribution environment. Of course, such a
patch should not have a negative impact on the behavior of the software.
testkraut can help to make a comparative assessment to alert the packager if
something starts to behave in unexpected ways.
