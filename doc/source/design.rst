Design
======

Goal
----

This aims to be a tool for testing real-world (integrated) software
environments with heterogeneous components from different vendors. It does
**not** try to be

- a unit test framework (you better pick one for you programming language of
  choice)
- a continuous integration testing framework (take a look at Jenkins or
  buildbot)
- a test framework for individual pieces of software (although that could work)

Instead, this tool is targeting the evaluation of fully deployed software on
"production" systems.  It aims at verifying proper functioning (or unchanged
behavior) of software systems comprised of components that were not
specifically designed or verified to work with each other.


Objectives
^^^^^^^^^^

- Gather comprehensive information about the software environment
- Integrate test case written in arbitrary languages or toolkits with minimal
  overhead
- Make it possible to easily deploy the system on users' machines to
  verify their environments

Dump of discussion with Satra
-----------------------------

- NiPyPE will do the provenance, incl. the gathering of system/env information
- anything missing in this domain needs to be added to nipype
- a test is a json file
- test code is stored directly in the json file
- tests will typically be nipype workflows
- individual tests will not depend on other tests (although a test runner could
  resolve data dependencies with outputs from other tests)
- a tests definition specifies: test inputs, test dependencies (e.g. software),
  and an (optional) evaluative statement

Dump of discussion with Alex
----------------------------

- A test fails or passes
- Evaluation assesses the quality of the test results (but doesn't necessarily
  let a test fail)
- Dashboard-level evaluation will provide highly aggregated analysis (e.g.
  distributions of evaluation metrics)
- Threshold levels for evaluation might need to be pulled from the dashboard
- Compare test output spec to actual content of the testbed after a test run
- Write little tool to check a test spec for comprehensive usage of all test
  output in evaluations

Generate test descriptions
--------------------------

via CDE
~~~~~~~

cde -o /tmp/betcde/ bet head.nii.gz brain
find /tmp/betcde/cde-root -executable -a -type f -a ! -name '*.cde' -a ! -name '*.so'


"depends": [
  {
    "type": "executable",
    "path": "$FSLDIR/bin/remove_ext",
    "dpkg": "fsl-5.0"
  }
]

via Tomoyo (Just an idea)
-------------------------

Tomoyo is a lightweight and easy-to-use MAC (Mandatory Access Control)
system for Linux, available in stock Linux kernel and tools shipped on
Debian.  In Learning mode it can easily collect provenance information
on what executables/libraries were used for a particular parent
process, what files were accessed, environment variables, etc.

Pros:
  should have virtually no run-time impact

Cons:
   might require admin privileges to get into learning mode and
   harvest result information

On SPECs
--------

All nested dicts -- except for leaves of the tree. That implies that no list
can be used anywhere inside the tree!!
