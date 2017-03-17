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
import shutil
import winreg

import vdf

REGISTRY_KEY_STEAM = r'SOFTWARE\Valve\Steam'
REGISTRY_KEY_STEAMPATH = 'SteamPath'

PATH_ARCHIVE = 'L:/archive/games/steam'	# TODO: Configurable.

FILENAME_LIBRARY_FOLDERS = 'steamapps/libraryfolders.vdf'


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
        return int(self._state['appID'])

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

    def move(self, dst):
        """Move game data to a new library."""
        assert isinstance(dst, Library)

        split_path = tuple(filter(
            None,
            os.path.split(os.path.normpath(self._installdir))
        ))
        assert len(split_path) == 1, "Non-relative installdir"

        new_path = self._copy_manifest(dst)
        try:
            self._copy_install_files(dst)
        except:
            os.remove(new_path)
            raise IOError("Move failed.")
        os.remove(self.path)
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
        """Copy game data and manifest to the archive."""
        archive = Archive() # There's only one anyway.

        self._archive_manifest(appmanifest, archive)
        try:
            self._archive_install_files(appmanifest, archive)
        except:
            self._backout__delete_manifest(appmanifest, archive)
            raise IOError("Archiving failed.")

    @staticmethod
    def _archive_manifest(appmanifest, archive):
        src = appmanifest.path
        dst = os.path.join(archive.path,
                           os.path.basename(appmanifest.path))
        shutil.copyfile(src, dst)

    @staticmethod
    def _archive_install_files(appmanifest, archive):
        src = appmanifest.install_path
        dst = os.path.join(archive.path,
                           os.path.basename(appmanifest.install_path))
        shutil.copytree(src, dst)

    @staticmethod
    def _backout__delete_manifest(appmanifest, archive):
        archived_manifest_path = os.path.join(
            archive.path,
            os.path.basename(appmanifest.path)
        )
        os.remove(archived_manifest_path)

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

    def select(self, regex):
        matches = []
        for name, manifest in self.games.items():
            if re.search(regex, name) is not None:
                matches.append(manifest)
        return matches


class Archive(Library):

    def __init__(self):
        super().__init__(PATH_ARCHIVE)

    @property
    def data_root(self):
        return PATH_ARCHIVE

    @staticmethod
    def restore(appmanifest, lib):
        """Copy game data from the archive."""
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


def get_steam_path():
    """Retrieve the Steam install path from the Windows registry."""
    key = winreg.HKEY_CURRENT_USER
    subkey = REGISTRY_KEY_STEAM
    access_flag = winreg.KEY_QUERY_VALUE

    steam_key = winreg.OpenKey(key, subkey, access=access_flag)
    value_typeflag = winreg.QueryValueEx(steam_key,
                                         REGISTRY_KEY_STEAMPATH)
    return os.path.normpath(value_typeflag[0])
