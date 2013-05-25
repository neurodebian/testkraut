.. -*- mode: rst; fill-column: 78; indent-tabs-mode: nil -*-
.. vi: set ft=rst sts=4 ts=4 sw=4 et tw=79:
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
  #
  #   See COPYING file distributed along with the testkraut package for the
  #   copyright and license terms.
  #
  ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

.. _chap_spec:

********
The SPEC
********

A test specification (or SPEC) is both primary input and output data for a test
case. As input data a SPEC defines test components, file dependencies, expected
test output, and whatever else that is necessary to describe a test case. As
test output, a SPEC is an annotated version of the input SPEC, with a detailed
descriptions of various properties of observed test components and results.
A SPEC is text file in :term:`JSON` format.

Path specifications for files can make use of environment variables which get
expanded appropriately. The special variable :envvar:`TESTKRAUT_TESTBED_PATH`
can be used to reference the directory in which a test is executed.

The following sections provide a summary of all SPEC components.

``authors``
===========

A :term:`JSON object`, where keys email addresses of authors of a SPEC and
corresponding values are the authors' names.

..
  ``dependencies``
  ================
..
  A :term:`JSON object`, where keys are platform IDs and corresponding values are
  platform-specific descriptions of software dependencies for a test case.
  The main purpose of this section is to allow for programmatic creation of test
  environments. Currently defined platforms are:
..
  ``deb``
    Debian-based systems using APT/dpkg as package manager. The dependency
    description is a :term:`JSON string` with a a package dependency list
    in the same format as the one used for the ``Depends`` field in the
    ``debian/control`` file in a Debian source package. For example::
..
      "dependencies": {"deb": "fsl (>= 4.0), matlab-spm (> 8)"}
..
  ``rpm``
    RedHat-derived systems using RPM as package manager. The dependency
    description is a :term:`JSON string` with a package dependency list
    in the same format as the one used for ```Requires`` lines in an RPM SPEC file.
..
  This section is identical in input SPEC and corresponding output SPEC.

``dependencies``
================

A :term:`JSON object` where keys are common names for dependencies of a test
case. Values are :term:`JSON object`\ s with fields described in the following
subsections.

..
  The ``executables`` section is altered
  in an output SPEC by adding an ``entity`` key to each executable's  :term:`JSON
  object`, with a :term:`JSON string` value, cross-referencing that executable
  with a corresponding entry in the ``entities`` section.

``location``
------------

Where is the respective namespace?

For executables this may contain absolute paths and/or environment variables
which will be expanded to their actual values during processing. Such variables
should be listed in the ``environment`` section.

``type``
--------

Could be an ``executable`` or a ``python_mod``.

``optional``
------------

A :term:`JSON boolean` indicating whether an executable is optional (``true``),
or required (``false``; default). Optional executables are useful for writing
tests that need to accommodate changes in the implementation of the to-be-tested
software.

``version_cmd``
---------------

A :term:`JSON string` specifying a command that will be executed to determine a
version of an executable that is added as value to the ``version`` field of the
corresponding entry for this executable in the ``entities`` section.  If an
output to ``stderr`` is found, it will be used as version. If no ``stderr``
output is found, the output to ``stdout`` will be used.

Alternatively, this may be a :term:`JSON array` with exactly two values, where
the first value is, again, the command, and the second value is a regular
expression used to extract matching content from the output of this command.
Output channels are evaluated in the same order as above (first ``stderr``, and
if no match is found ``stdout``).

``version_file``
----------------

A :term:`JSON string` specifying a file name. The content of this file will be
added as value to the ``version`` field of the corresponding entry for this
executable in the ``entities`` section.

Alternatively, this may be a :term:`JSON array` with exactly two values, where
the first value is, again, a file name, and the second value is a regular
expression used to extract matching content from this file as a version.

Example
-------
::

 "executables": {
    "$FSLDIR/bin/bet": {
      "version_cmd": [
            "$FSLDIR/bin/bet2",
            "BET \\(Brain Extraction Tool\\) v(\\S+) -"
      ]
    }, 
    "$FSLDIR/bin/bet2": {
      "version_file": "$FSLDIR/etc/fslversion"
    }


``description``
===============

A :term:`JSON string` with a verbal description of the test case. The
description should contain information on the nature of the test, any input
data files, and where to obtain them (if necessary).

This section is identical in input SPEC and corresponding output SPEC.

``entities``
============

A :term:`JSON object`, where keys are unique identifiers (:term:`JSON string`),
and values are :term:`JSON object`\ s. Identifiers are unique but identicial
for identical entities, even across systems (e.g. the file sha1sum). All items
in this section describe entities of relevance in the context of a test run --
required executables, their shared library dependencies, script interpreters,
operating system packages providing them, and so on. There are various
categories of values in this section that can be distinguished by their
``type`` field value, and which are described in the following subsections.

This section only exists in output SPECs.

``type``: ``binary``
--------------------

This entity represents a compiled executable. The following fields are supported

``path`` (:term:`JSON string`)
  Executable path as specified in the input SPEC.

``provider``  (:term:`JSON string`)
  Identifier/key of an operating system package entry in the ``entities``
  section.

``realpath`` (:term:`JSON string`)
  Absolute path to the binary, with all variables expanded and all symlinks
  resolved.

``sha1sum`` (:term:`JSON string`)
  SHA1 hash of the binary file. This is identical to the item key.

``shlibdeps`` (:term:`JSON array`)
  Identifiers/keys of shared library dependency entries in the ``entities``
  section.

``version`` (:term:`JSON string`)
  Version output generated from the ``version_cmd`` or ``version_file`` settings
  in the input SPEC for the corresponding executable.


``type``: ``deb`` or ``rpm``
----------------------------

This entity represents a DEB or RPM package. The following fields are supported

``arch`` (:term:`JSON string`)
  Identifier for the hardware architecture this package has been compiled for.

``name`` (:term:`JSON string`)
  Name of the package.

``sha1sum`` (:term:`JSON string`)
  SHA1 hash for the package.

``vendor`` (:term:`JSON string`)
  Name of the package vendor.

``version`` (:term:`JSON string`)
  Package version string.

``type``: ``library``
---------------------

This entity represent a shared library. The types and meaning of the supported
fields are identical to ``binary``-type entities, except that there is no
``version`` field.

``type``: ``script``
--------------------

This entity represents an interpreted script. The types and meaning of the
supported fields are identical to ``binary``-type entities, except that there
is no ``shlibdeps`` field, but instead:

``interpreter``  (:term:`JSON string`)
  Identifier/key for the script interpreter entry in the ``entities``
  section.

``environment``
===============

A :term:`JSON object`, where keys represent names of variables in the system
environment. If the corresponding value is a string the respective variable
will be set to this value prior test execution. If the value is ``null`` any
existing variable of such name will be unset. If the value is ``true`` the
presence of this variable is required and its value is recorded in the protocol.
If the value is ``false``, the variable is not required and its (optional)
value is recorded.

``comparisons``
===============

yet to be determined

``id``
======

A :term:`JSON string` with an ID that uniquely identifies the test case.
In a test library the test case needs to be stored in a directory whose name is
equal to this ID, while the SPEC is stored in a file named ``spec.json`` inside
this directory. While not strictly required, it is preferred that this ID is
"human-readable" and carries an reasonable amount of semantic information. For
example: ``fsl-mcflirt`` is a test the is concerned with the MCFlirt component
of the FSL suite.

This section is identical in input SPEC and corresponding output SPEC.

``inputs``
==========

A :term:`JSON object`, where keys represent IDs of required inputs for a test
case. Corresponding values are, again,  :term:`JSON object`\ s with a mandatory
``type`` field. The value of ``type`` is a :term:`JSON string`
identifying the type of input. Currently only type ``file`` is supported. For a
``file``-type input the following additional fields should be present:

``sha1sum`` (:term:`JSON string`)
  SHA1 hash that uniquely identifies the input file.

``tags`` (:term:`JSON array`)
  Optional list of :term:`JSON string`\ s with tags categorizing the input
  (see :ref:`tags <chap_output_tags>`).

``url`` (:term:`JSON string`)
  URL where the respective file can be downloaded.

``value`` (:term:`JSON string`)
  name of the input file.

Example
-------
::

  "inputs": {
    "head.nii.gz": {
      "sha1sum": "41d817176ceb99ac051d8bd066b500f3fb89be89", 
      "type": "file", 
      "value": "head.nii.gz"
    }
  }


``outputs``
===========

This section is very similar to the ``inputs`` section, and may contain similar
information in matching fields with identical semantics. In contrast to
``inputs`` this section can be substantially extended in the output SPEC.  For
example, output files may not have a SHA1 hash specified in the input SPEC, but
a SHA1 hash for the actually observed output file will be stored in the
output's ``sha1sum`` field. Most importantly, for any output file whose
``tags`` match one or more of the configured :ref:`fingerprint generators
<chap_output_fingerprinting>` a ``fingerprints`` field will be added to the
:term:`JSON object` for the corresponding output file. 

``fingerprints``
----------------

The value of this field is a :term:`JSON object` where keys are names of
fingerprint generators, and values should be :term:`JSON object`\ s with a
custom structure that is specific to the particular type of fingerprint.
All fingerprints should contain a ``version`` field (:term:`JSON number`;
integer) that associates any given fingerprint with the implementation
of the generator that created it.

``processes``
=============

A :term:`JSON object` describing causal relationships among test components.
Keys are arbitrary process IDs. Values are :term:`JSON object`\ s with fields
described in the following subsections.

This section is currently not modified or extended during a test run.

``argv`` (:term:`JSON array`)
  ``argv``-style command specification for a process. For example::

    ["$FSLDIR/bin/bet", "head.nii.gz", "brain", "-m"]

``executable`` (:term:`JSON string`)
  ID/key of the associated executable from the ``executables`` section.

``generates`` (:term:`JSON array`)
  IDs/keys of output files (from the ``outputs`` section) created by this
  process.

``started_by`` (:term:`JSON string`)
  ID/key of the process (from the same section) that started this process.

``uses`` (:term:`JSON array`)
  IDs/keys of input files (from the ``inputs`` section) required by this
  process.

Example
-------
::

  "0": {
    "argv": [
      "$FSLDIR/bin/bet2", 
      "head", 
      "brain", 
      "-m"
    ], 
    "executable": "$FSLDIR/bin/bet2", 
    "generates": [
      "brain.nii.gz", 
      "brain_mask.nii.gz"
    ], 
    "started_by": 1, 
    "uses": [
      "head.nii.gz"
    ]
  }, 


``system``
==========

A :term:`JSON object` listing various properties of the computational
environment a test was ran in. This section is added by the test runner and
only exists in output SPECs.

``tests``
========

A :term:`JSON array` of :term:`JSON object`\ s describing the actual test cases.
All (sub-)test cases are executed in order of appearance in the array, in the
same test bed, using the same environment. Multiple sub-tests can be used to
split tests into sub parts to improve error reporting, while minimizing test
SPEC overhead. However, output fingerprinting is only done once *after* all
subtests have completed successfully.

For each :term:`JSON object` describing a sub-test, the mandatory ``type``
field identifies the kind of test case and the possible content of this section
changes accordingly. Supported scenarios are described in the following
subsections.

For any test type, a test can be marked as an expected failure by adding a field
``shouldfail`` and setting its value to ``true``.

An optional field ``id`` can be used to assign a meaningful identifier to a
subtest that is used in the test protocol. If no ``id`` is given, as subtest's
index in the tests array is used as identifier.

``type``: ``shell``
-------------------

The test case is a shell command. The command is specified in a text field
``code``, such as::

  "code": "$FSLDIR/bin/bet head.nii.gz brain -m"

In the output SPEC of a test run this section is amended with the
following fields:

``exitcode`` (:term:`JSON number`; integer)
  Exit code for the executed command.

``type``: ``python``
--------------------

Explain me

``type``: ``nipype``
--------------------

Explain me


``version``
===========

A :term:`JSON number` (integer) value indicating the version of a SPEC. This version
must be incremented whenever a change to a SPEC is done.

This section is identical in input SPEC and corresponding output SPEC.
