# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the testkraut package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
""""""

__docformat__ = 'restructuredtext'

import logging
lgr = logging.getLogger(__name__)
import os

class PkgManager(object):
    """Simple abstraction layer to query local package managers"""
    def __init__(self):
        self._mode = None
        try:
            import apt
            self._native_pkg_cache = apt.Cache()
            self._mode = 'deb'
        except ImportError:
            from .utils import run_command
            # it could still be debian, but without python-apt
            ret = run_command('dpkg --version')
            self._native_pkg_cache = None
            if ret['retval'] == 0:
                self._mode = 'deb'
                lgr.warning("Running on Debian platform but no python-apt "
                            "package found -- only limited information is "
                            "available.")

    def get_pkg_name(self, filename):
        """Return the name of a package providing a file (if any).

        Returns None if no package provides this file, or no package manager is
        available.
        """
        if os.path.exists(filename):
            # if the file actually exists try resolving symlinks
            filename = os.path.realpath(filename)
        if self._mode == 'deb':
            return _get_debian_pkgname(filename)
        return None

    def get_pkg_info(self, pkgname):
        """Returns a dict with information on a given package."""
        info = dict(name=pkgname)
        if self._mode == 'deb':
            return self._get_debian_pkginfo(pkgname, info)
        return info

    def _get_debian_pkginfo(self, pkgname, debinfo):
        apt = self._native_pkg_cache
        if not apt is None:
            pkg = apt[pkgname].installed
            if pkg is None:
                # no such package installed
                return debinfo
            debinfo['version'] = pkg.version
            debinfo['sha1sum'] = pkg.sha1
            debinfo['arch'] = pkg.architecture
            origin = pkg.origins[0]
            debinfo['origin'] = origin.origin
            debinfo['origin_archive'] = origin.archive
            debinfo['origin_site'] = origin.site
            debinfo['origin_trusted'] = origin.trusted
        return debinfo

    def get_platform_name(self):
        """Returns the local package manager type.

        For example, 'deb', 'rpm', or None if no supported package manager
        was found.
        """
        return self._mode


def _get_debian_pkgname(filename):
    from .utils import run_command
    # provided by a Debian package?
    pkgname = None
    try:
        ret = run_command('dpkg -S %s' % filename)
    except OSError:
        return None
    if not ret['retval'] == 0:
        return None
    for line in ret['stdout']:
        lspl = line.split(':')
        if lspl[0].count(' '):
            continue
        pkgname = lspl[0]
        break
    return pkgname
