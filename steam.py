"""Basic administrative tools for working with Steam games.

Provides methods for listing steam libraries and the games contained
in them, archiving and restoring from archive.


Usage
-----

    >>> from gameadmin import steam
    >>> libs = steam.get_libraries()

Archive the first listed game in the first library:

    >>> lib = libs[0]
    >>> game = lib.games[0]
    >>> lib.archive(game)


Notes
-----

This is all very ad-hoc as it was made to quickly shuffle games in and
out of libraries for disk capacity reasons so it's not really
"production" ready. That said, it does work as far as I've used it.

See also:

  - https://github.com/Holiverh/python-valve/blob/master/valve/steam/client.py
"""

import os
import re
import glob
import psutil
import shutil
import warnings
import winreg

import humanize
import vdf

REGISTRY_KEY_STEAM = r'SOFTWARE\Valve\Steam'
REGISTRY_KEY_STEAMPATH = 'SteamPath'

PATH_ARCHIVE = 'L:/archive/games/steam'	# TODO: Configurable.

FILENAME_LIBRARY_FOLDERS = 'steamapps/libraryfolders.vdf'


# NOTE: It might be more semantically accurate to call this a game.
#       It's OK for a game to be built from an AppManifest...
class AppManifest(object):
    """Encapsulation of metadata in appmanifest ACF."""

    def __init__(self, path):
        self.path = path
        with open(path, 'r') as f:
            self._metadata = vdf.load(f)

    @property
    def archive_path(self):
        return os.path.join(PATH_ARCHIVE, self._installdir)

    @property
    def id(self):
        try:
            return int(self._state['appID'])
        except KeyError:
            # We assume there is an app ID, but maybe lowercase.
            return int(self._state['appid'])

    @property
    def _installdir(self):
        try:
            return self._state['installdir']
        except KeyError:
            return self._state['InstallDir']

    @property
    def install_path(self):
        root_dir = os.path.join(os.path.dirname(self.path), 'common')
        return os.path.join(root_dir, self._installdir)

    @property
    def name(self):
        try:
            return self._state['name']
        except KeyError:
            try:
                # Try using UserConfig, not all games have top-level names
                return self._state['UserConfig']['name']
            except KeyError:
                # Otherwise try and derive it from the install path.
                return os.path.basename(self.install_path)

    @property
    def size(self):
        return int(self._state['SizeOnDisk'])

    @property
    def _state(self):
        """Steam Application state dictionary."""
        return self._metadata['AppState']

    def archive(self):
        """Copy game data and manifest to the archive."""
        abort_if_steam_is_running() # TODO: Necessary?

        archive = Archive() # There's only one anyway.

        self._archive_manifest(archive)
        try:
            self._archive_install_files(archive)
        except:
            self._backout__delete_manifest(archive)
            raise IOError("Archiving failed.")

    def _archive_manifest(self, archive):
        src = self.path
        dst = os.path.join(archive.path,
                           os.path.basename(self.path))
        shutil.copyfile(src, dst)

    def _archive_install_files(self, archive):
        src = self.install_path
        dst = os.path.join(archive.path,
                           os.path.basename(self.install_path))
        shutil.copytree(src, dst)

    def _backout__delete_manifest(self, archive):
        archived_manifest_path = os.path.join(
            archive.path,
            os.path.basename(self.path)
        )
        os.remove(archived_manifest_path)

    def move(self, dst, force=False, fast=False):
        """Move game data to a new library."""
        # TODO: Introduce a fast version of this that doesn't copy
        #       if on same filesystem.
        abort_if_steam_is_running()

        assert isinstance(dst, Library)

        if not force:
            abort_if_not_archived(self)

        # Some older manifests have non-relative install paths. It's
        # best to just change these at source...
        split_path = tuple(filter(
            None,
            os.path.split(os.path.normpath(self._installdir))
        ))
        msg = "Non-relative installdir in appmanifest."
        assert len(split_path) == 1, msg

        if fast:
            if not same_partition(self.install_path,
                                  dst.install_path):
                # It'll be copied anyway.
                msg = ("Fast move not possible between partitions; "
                       "ignoring `fast=True`")
                warnings.warn(msg)
                fast = False

        new_path = self._copy_manifest(dst)
        try:
            if fast:
                self._move_install_files(dst)
            else:
                # Copy the installation directory.
                self._copy_install_files(dst)
        except:
            os.remove(new_path)
            raise IOError("Move failed.")

        os.remove(self.path)
        if not fast:
            # We copied; safe to remove the source.
            shutil.rmtree(self.install_path)

    def _copy_manifest(self, lib):
        src = self.path
        dst = os.path.join(lib.path, 'steamapps',
                           os.path.basename(self.path))
        shutil.copyfile(src, dst)
        return dst

    def _copy_install_files(self, lib):
        src = self.install_path
        dst = os.path.join(lib.install_path,
                           os.path.basename(self.install_path))
        shutil.copytree(src, dst)

    def _move_install_files(self, lib):
        src = self.install_path
        dst = os.path.join(lib.install_path,
                           os.path.basename(self.install_path))
        shutil.move(src, dst)


class Library(object):

    def __init__(self, path):
        self.path = os.path.normpath(os.path.expanduser(path))

    @property
    def install_path(self):
        return os.path.join(self.data_root, 'common')

    @property
    def size(self):
        return sum(am.size for am in self.get_manifests())

    @property
    def games(self):
        return {am.name: am for am in self.get_manifests()}

    @property
    def data_root(self):
        return os.path.join(self.path, 'steamapps')

    @property
    def _acf_glob(self):
        return os.path.join(self.data_root, '*.acf')

    def archive(self, appmanifest):
        appmanifest.archive()
    archive.__doc__ = AppManifest.archive.__doc__

    def get_manifests(self):
        return list(map(AppManifest, glob.glob(self._acf_glob)))

    def as_table(self, sort_by=('name.lower',), fmt='human'):

        def sort_key(_manifest):
            values = []
            for attr in sort_by:
                if attr == 'name.lower':
                    attr = 'name'
                    values.append(getattr(_manifest, attr).lower())
                elif attr == 'size.desc':
                    attr = 'size'
                    values.append(getattr(_manifest, attr) * -1)
                else:
                    values.append(getattr(_manifest, attr))
            return tuple(values)

        try:
            fmt_string = {
                'human': '{:>50s} | {:8.2f} | {:d}',
            }[fmt]
        except KeyError:
            raise ValueError("Format not recognised.")

        rows = []
        for manifest in sorted(self.get_manifests(), key=sort_key):
            if len(manifest.name) > 50:
                name = manifest.name[:47] + '...'
            else:
                name = manifest.name
            rows.append(
                    fmt_string.format(name,
                                      manifest.size / 1024**3,
                                      manifest.id)
            )
        rows.append(' '*51 + '|' + ' '*10 + '|')
        rows.append(
            '{:>50s} | {:8.2f} |'.format('TOTAL', self.size / 1024**3)
        )
        return os.linesep.join(rows)

    def issues(self):
        """Summarise issues with the library.

        Returns a dict where keys map to the following problems:

            orphan-dirs
            :   contains list of directories not present in an
                AppManifest. The best way to fix this is install the
                game in Steam to this library and let it discover
                existing data.

            dangling-manifests
            :	contains list of manifests where the directory is not
                present in this library.
        """
        issues_dict = {}

        issues_dict['orphan-dirs'] = list(sorted(
            self._orphan_directories()
        ))

        issues_dict['dangling-manifests'] = list(
            self._dangling_manifests()
        )

        return issues_dict

    def _orphan_directories(self):
        # Return set of directories not accounted for in AppManifests
        if os.name != 'nt':
            # TODO: Improved method of detecting OS context. Libraries
            #       might exist on Linux or Windows (or OSX...?) and
            #       we might be running this from either.
            #
            # This method of checking is not necessarily valid for
            # POSIX systems. AppManifests may contain case-insensitive
            # paths and this is accomodated here.
            raise NotImplementedError("POSIX not supported.")

        for root, dnames, fnames in os.walk(self.install_path):
            fs_dname_set_preserve_case = set(dnames)
            fs_dname_set = set(map(str.lower, dnames))
            break	# We only care about the directories in root.

        am_dname_set = set(
            str.lower(os.path.basename(game.install_path))
            for game in self.games.values()
        )

        return set(
            dname
            for dname in fs_dname_set_preserve_case
            if dname.lower() in fs_dname_set.difference(am_dname_set)
        )

    def _dangling_manifests(self):
        path = self.install_path
        return set(
            appmanifest
            for appmanifest in self.games.values()
            if not appmanifest.install_path.startswith(path)
        )

    def remove(self, appmanifest, force=False):
        """Remove the game associated with this appmanifest.

        Raises an exception if this game is not archived unless force
        is True.
        """
        abort_if_steam_is_running()

        archive = Archive()
        if not force:
            abort_if_not_archived(appmanifest)
        else:
            os.remove(appmanifest.path)
            shutil.rmtree(appmanifest.install_path)

    def select(self, regex):
        matches = []
        for name, manifest in self.games.items():
            if re.search(regex, name) is not None:
                matches.append(manifest)
        return matches

    def __str__(self):
        # Simple string representation giving location and size.
        drive = os.path.splitdrive(self.install_path)[0].upper()
        count = len(self.games)
        size = humanize.naturalsize(self.size)
        return "Steam Library ({}, {} games, {})".format(drive,
                                                         count,
                                                         size)


class Archive(Library):

    def __init__(self):
        super().__init__(PATH_ARCHIVE)

    @property
    def data_root(self):
        return os.path.normpath(PATH_ARCHIVE)

    @property
    def install_path(self):
        """Path of game install directories in Archive.
        """
        return self.data_root

    def remove(self, appmanifest):
        """Remove game data from archive."""

        # Check we're actually looking at an archived appmanifest.
        ampath = os.path.normpath(appmanifest.path)
        common_prefix = os.path.commonprefix([ampath, self.data_root])
        if common_prefix != self.data_root:
            raise ValueError("AppManifest is not in archive.")

        # Remove the AppManifest, followed by the archived installdir
        os.remove(appmanifest.path)
        shutil.rmtree(os.path.join(
            self.data_root,
            os.path.basename(appmanifest.install_path)
        ))

    @staticmethod
    def restore(appmanifest, lib):
        """Copy game data from the archive."""
        abort_if_steam_is_running()

        installdir = os.path.basename(appmanifest.install_path)
        src = os.path.join(os.path.dirname(appmanifest.path),
                           installdir)
        dst = os.path.join(lib.install_path, installdir)
        shutil.copytree(src, dst)


def get_libraries():
    """Steam library factory."""
    lib_paths = [get_steam_path()]
    idx_path = os.path.join(lib_paths[0], FILENAME_LIBRARY_FOLDERS)
    with open(idx_path, 'r') as f:
        dct = vdf.load(f)['LibraryFolders']

    i = 1
    while True:
        try:
            lib_paths.append(os.path.normpath(dct[str(i)]))
        except KeyError:
            break
        i += 1

    return list(map(Library, lib_paths))


def same_partition(path1, path2):
    """Determine whether two paths are on the same partition.

    This compares the path structure to see whether they have a common
    root. No doubt some weirdness of application will break this.
    """

    if os.name != 'nt':
        # TODO: See Library._orphan_directories TODO.
        raise NotImplementedError("Algorithm not implemented.")

    common_prefix = os.path.commonprefix(list(map(
        os.path.normpath,
        map(str.lower, [path1, path2])
    )))

    if common_prefix:
        return True
    else:
        return False


def get_steam_path():
    """Retrieve the Steam install path from the Windows registry."""
    key = winreg.HKEY_CURRENT_USER
    subkey = REGISTRY_KEY_STEAM
    access_flag = winreg.KEY_QUERY_VALUE

    steam_key = winreg.OpenKey(key, subkey, access=access_flag)
    value_typeflag = winreg.QueryValueEx(steam_key,
                                         REGISTRY_KEY_STEAMPATH)
    return os.path.normpath(value_typeflag[0])


def abort_if_not_archived(appmanifest):
    # TODO: This is begging to be a decorator.
    archive = Archive()
    if appmanifest.name not in archive.games.keys():
        raise RuntimeError("Game is not archived; aborting!")


def abort_if_steam_is_running():
    # TODO: This is begging to be a decorator.
    if steam_is_running():
        raise RuntimeError(
            "Steam is running; probably a good idea to exit..."
        )


def steam_is_running():
    return 'Steam.exe' in set([ps.name()
                               for ps in psutil.process_iter()])
