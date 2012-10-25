
def get_pkg_executables():
    import apt
    cache = apt.Cache()

    return list(
        itertools.chain(
            *[[p for p in pkg.installed_files
                    if not os.path.isdir(p) and os.access(p, os.X_OK)]
                for pkg in cache if pkg.is_installed]))

