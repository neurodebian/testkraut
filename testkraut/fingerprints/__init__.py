# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Module with fingerprint generators"""

__docformat__ = 'restructuredtext'

import logging
lgr = logging.getLogger(__name__)
from .base import fp_file as _fp_file

_tag2fx = {}

def get_fingerprinters(tag):
    """Return a sequence of fingerprint functors for a specific tag.
    """
    if not len(_tag2fx):
        # charge
        from testkraut import cfg
        tags = set(cfg.options('system fingerprints')).union(cfg.options('fingerprints'))
        for tag_ in tags:
            fp_tag = set()
            for fps_str in cfg.get('system fingerprints', tag_, default="").split() \
                         + cfg.get('fingerprints', tag_, default="").split():
                fps_comp = fps_str.split('.')
                try:
                    mod = __import__('.'.join(fps_comp[:-1]), globals(), locals(),
                                     fps_comp[-1:], -1)
                    fps = getattr(mod, fps_comp[-1])
                except:
                    lgr.warning(
                        "ignoring invalid fingerprinting function '%s' for tag '%s'"
                        % (fps_str, tag_))
                fp_tag.add(fps)
            _tag2fx[tag_] = fp_tag
    fprinters = _tag2fx.get(tag, set())
    fprinters.add(_fp_file)
    return fprinters


def proc_fingerprint(fingerprinter, fingerprints, filename, tags=None):
    if tags is None:
        tags = []
    finger_name = fingerprinter.__name__
    if finger_name.startswith('fp_'):
        # strip common name prefix
        finger_name = finger_name[3:]
    lgr.debug("generating '%s' fingerprint" % finger_name)
    # run it, catch any error
    try:
        fprint = {}
        fingerprints[finger_name] = fprint
        # fill in a dict to get whetever info even if an exception
        # occurs during a latter stage of the fingerprinting
        fingerprinter(filename, fprint, tags)
    except Exception, e:
        fprint['__exception__'] = '%s: %s' % (type(e), e.message)
        # XXX maybe better a warning?
        lgr.debug("ignoring exception '%s' while fingerprinting '%s' with '%s'"
                  % (str(e), filename, finger_name))

