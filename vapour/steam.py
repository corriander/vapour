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
import abc
import os
import re
import glob
import math
import shutil
import textwrap
import warnings

import humanize
import vdf

from .facades import Steam, DiskManagement, Settings


PATH_ARCHIVE = Settings().collections['archives']

FILENAME_LIBRARY_FOLDERS = 'steamapps/libraryfolders.vdf'

class Model(abc.ABC):

    @abc.abstractproperty
    def data_attributes(self):
        return tuple()

    def __iter__(self):
        for key in self.data_attributes:
            yield (key, getattr(self, key))


# NOTE: It might be more semantically accurate to call this a game.
#       It's OK for a game to be built from an AppManifest...
class AppManifest(Model):
    """Encapsulation of metadata in appmanifest ACF."""

    data_attributes = (
        'id',
        'name',
        'manifest_path',
        'install_path',
        'size',
    )

    def __init__(self, path, lib=None):
        self.path = path
        self.lib = lib
        with open(path, 'r') as f:
            self._metadata = vdf.load(f)

    @property
    def manifest_path(self):
        return self.path

    @property
    def archive_path(self):
        path = os.path.normpath(os.path.dirname(self.path))
        if path not in [os.path.normpath(p) for p in PATH_ARCHIVE]:
            archive_path = PATH_ARCHIVE[0]
        else:
            archive_path = path
        return os.path.join(path, self._installdir)

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
        if self.lib is None or not isinstance(self.lib, Archive):
            root_dir = os.path.join(os.path.dirname(self.path), 'common')
        else:
            root_dir = os.path.join(os.path.dirname(self.path))
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

    def archive(self, archive=None):
        """Copy game data and manifest to the archive."""
        abort_if_steam_is_running() # TODO: Necessary?

        if archive is None:
            archive = Archive() # Use the default

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

    def inspect_size(self):
        """Inspect the size of the game installation.

        This can be useful detecting discrepancies between the size
        reported by the app manifest and the real size on disk (e.g.
        missing or extra data).
        """
        return get_directory_size(self.install_path)

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

    def remove(self):
        """Remove app manifest and data from the associated library.
        """
        self.lib.remove(self)

    def size_delta(self):
        """Get the difference in size between the manifest and data.
        """
        return self.size - self.inspect_size()

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

    def __hash__(self):
        return hash((self.path, str(sorted(self._metadata))))

    def __eq__(self, other):
        return self._metadata == other._metadata


class Library(Model):

    disk_management = DiskManagement()

    data_attributes = (
        'path',
        'install_path',
        'apps_path',
        'size',
        'free_bytes',
        'games'
    )

    def __init__(self, path):
        self.path = os.path.normpath(os.path.expanduser(path))

    @property
    def free(self):
        """Free disk space available to this library."""
        return humanize.naturalsize(self.free_bytes)

    @property
    def free_bytes(self):
        """Free disk space available to this library in Bytes."""
        return self.disk_management.get_free_space(
            self.install_path
        )

    @property
    def install_path(self):
        """Location of game data.

        Deprecated; use d_path"""
        return os.path.join(self.apps_path, 'common')

    @property
    def apps_path(self):
        """Contains manifests (and game data in a nested directory)."""
        return os.path.join(self.path, 'steamapps')

    @property
    def size(self):
        """Total registed size of library.

        Warning: This may differ from actual size as this is a summary
        of all sizes in the game manifests, not the actual data in the
        disk. For example, if a manifest is deleted, the game data
        will still be there.
        """
        return sum(am.size for am in self.game_lookup.values())

    @property
    def games(self):
        return self.get_manifests()

    @property
    def game_lookup(self):
        """Dictionary of games keyed by name."""
        return {am.name: am for am in self.get_manifests()}

    @property
    def _acf_glob(self):
        return os.path.join(self.apps_path, '*.acf')

    def archive(self, appmanifest):
        appmanifest.archive()
    archive.__doc__ = AppManifest.archive.__doc__

    def get_manifests(self):
        """Return a list of manifests found in the apps_path."""
        manifests = []
        for path in glob.glob(self._acf_glob):
            manifests.append(AppManifest(path, lib=self))
        return manifests

    def as_table(self, sort_by=('name.lower',), fmt='human'):
        """Summarise library as a table.

            sort_by: sequence of strings
                Specifies the attribute of a game to sort by.
                'name.lower' and 'size.desc' are special cases for
                normalised name sorting and largest to smallest.

            fmt: string in set {'human',}
                Defines the format of the table contents.
        """
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

    def inspect_size(self):
        """Inspect the size of the library directory.

        This is useful for identifying discrepancies between the size
        reported by app manifests (available via `size` property) and
        the real on-disk size.
        """
        return get_directory_size(self.install_path)

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

            size-discrepancy
            :   contains any identified size discrepancies between
                metadata and size on disk.
        """
        issues_dict = {}

        issues_dict['orphan-dirs'] = list(sorted(
            self._orphan_directories()
        ))

        issues_dict['dangling-manifests'] = list(
            self._dangling_manifests()
        )

        issues_dict['size-discrepancy'] = self._size_discrepancies()

        # Don't bother reporting on duplicates.
        d = issues_dict['size-discrepancy'].copy()
        for game in d:
            if game == 'lib':
                continue
            if self.game_lookup[game] in issues_dict['dangling-manifests']:
                issues_dict['size-discrepancy'].pop(game)

        return issues_dict

    def issues_report(self, issues_dict=None):
        """Human-readable report of issues with the library."""

        lines = []

        if issues_dict is None:
            issues_dict = self.issues()

        if issues_dict['orphan-dirs']:
            blurb = """
            Orphaned Game Data
            ------------------

            The following game directories exist but Steam doesn't
            appear to know about them:
            """
            lines.append(textwrap.dedent(blurb))
            for d in issues_dict['orphan-dirs']:
                size = humanize.naturalsize(
                    get_directory_size(
                        os.path.join(self.install_path,
                                     d)
                    )
                )
                lines.append('  - {} ({})'.format(d, size))

        if issues_dict['dangling-manifests']:
            blurb = """
            Dangling Manifests
            ------------------

            The following games are registered by Steam, but there
            doesn't appear to be any game data present:
            """
            lines.append(textwrap.dedent(blurb))
            for am in issues_dict['dangling-manifests']:
                lines.append('  - {} (id: {})'.format(am.name, am.id))

        if issues_dict['size-discrepancy']:
            def hr_delta(delta):
                if delta < 0:
                    relative = "bigger"
                elif delta > 0:
                    relative = "smaller"
                elif math.isnan(delta):
                    relative = "unknown"

                if relative != "unknown":
                    delta = humanize.naturalsize(abs(delta))
                    return "{} {}".format(delta, relative)

                else:
                    return "unknown; only have size"

            header = """
            Size Discrepancies
            ------------------

            Library is {} than Steam thinks it is.
            """

            lib_delta = issues_dict['size-discrepancy'].pop('lib')
            if lib_delta:
                lines.append(
                    textwrap.dedent(header.format(hr_delta(lib_delta)))
                )

                if issues_dict['size-discrepancy']:
                    lines.append(textwrap.dedent("""
                        The following games are known about by Steam,
                        but there appears to be a significant
                        difference in size between the content of the
                        app manifest and the size on disk (>0.1%):
                    """))

                for game, delta in issues_dict['size-discrepancy'].items():
                    lines.append(
                        "  - {} ({} on disk)".format(
                            game,
                            hr_delta(delta)
                        )
                    )

        return '\n'.join(lines)

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
            for game in self.game_lookup.values()
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
            for appmanifest in self.game_lookup.values()
            if not os.path.exists(appmanifest.install_path)
        )

    def _size_discrepancies(self):
        d = {'lib': self.size - self.inspect_size()}
        for game, am in self.game_lookup.items():
            delta = am.size_delta()
            if not am.size:
                d[game] = math.nan
            elif delta != 0 and delta / float(am.size) > 0.001:
                d[game] = delta
        return d

    def contains(self, regex):
        """Test whether the library contains a game matching regex.
        """
        if self.select(regex):
            return True
        else:
            return False

    def remove(self, appmanifest, force=False):
        """Remove the game associated with this appmanifest.

        Raises an exception if this game is not archived unless force
        is True.
        """
        abort_if_steam_is_running()

        archive = Archive()
        if not force:
            abort_if_not_archived(appmanifest)
        os.remove(appmanifest.path)
        shutil.rmtree(appmanifest.install_path)

    def select(self, regex):
        matches = []
        for name, manifest in self.game_lookup.items():
            if re.search(regex, name) is not None:
                matches.append(manifest)
        return matches

    def __get_drive_caption(self):
        return os.path.splitdrive(self.install_path)[0].upper()

    def __str__(self):
        # Simple string representation giving location and size.
        drive = self.__get_drive_caption()
        count = len(self.game_lookup)
        size = humanize.naturalsize(self.size)
        return "Steam Library ({}, {} games, {})".format(drive,
                                                         count,
                                                         size)

    def __repr__(self):
        return "<{}(path='{}')>".format(self.__class__.__name__,
                                        self.path)


class Archive(Library):

    def __init__(self, path=PATH_ARCHIVE[0]):
        super().__init__(path)

    @property
    def apps_path(self):
        return os.path.normpath(self.path)

    @property
    def install_path(self):
        """Path of game install directories in Archive.

        """
        return self.apps_path

    def get_archived_game_size(self, appmanifest):
        return get_directory_size(appmanifest.archive_path)

    def issues(self):
        # Adds a redundant archive data check.
        issues_dict = super().issues()

        redundant_games = []
        for name in self.game_lookup:
            hits = locate_game(name)
            redundant_games.extend(
                [(lib.select(name)[0], lib) for lib in hits]
            )

        if redundant_games:
            issues_dict['redundant-data'] = redundant_games

        return issues_dict

    def issues_report(self):
        issues_dict = self.issues()
        string = super().issues_report()

        extra_lines = []

        if issues_dict.get('redundant-data', ()):
            blurb = """
            Redundant Data
            --------------

            The following games are archived, but are also installed
            in one or more game library:
            """
            extra_lines.append(textwrap.dedent(blurb))
            for am, lib in issues_dict['redundant-data']:
                extra_lines.append(
                    '  - {} (id: {}; lib: {})'.format(am.name, am.id, lib)
                )

        string = '\n'.join([string] + extra_lines)
        return string.replace('Steam', '<Archive>')

    def remove(self, appmanifest=None, pattern=None):
        """Remove games from archive.

        A single game may be specified by appmanifest, and/or games
        matching the pattern.

            appmanifest: AppManifest
                An app manifest present in the archive. If the
                appmanifest is not in the archive, the remove
                operation is aborted.

            pattern: str
                A .select() compatible expression for selecting games
                by name.
        """
        if all(arg is None for arg in (appmanifest, pattern)):
            raise TypeError("Either appmanifest or pattern "
                            "must have a meaningful value.")

        appmanifests_to_remove = []

        # Handle the single appmanifest
        if appmanifest is not None:
            # Check we're actually looking at an archived appmanifest.
            common_prefix = os.path.commonprefix(
                [appmanifest.install_path, self.apps_path]
            )
            if common_prefix != self.apps_path:
                raise ValueError("AppManifest is not in archive.")
            appmanifests_to_remove.append(appmanifest)

        # Handle patterns
        if pattern is not None:
            appmanifests_to_remove.extend(self.select(pattern))
            if not appmanifests_to_remove:
                # We obviously didn't get an explicit AppManifest and
                # nothing was returned by select.
                print("No matching app manifests to remove.")
                return

        # Prompt before removal (we must have 1+ at this point).
        prompt_lines = ["The following will be removed:\n"]
        for am in appmanifests_to_remove:
            prompt_lines.append("\t{}".format(am.name))
        prompt_lines.append("\nProceed with removal (Y)? ")
        ans = input('\n'.join(prompt_lines))
        if ans != 'Y':
            print("Removal aborted.")
            return

        # Proveed with the removal.
        for am in appmanifests_to_remove:
            # Remove the AppManifest, followed by the data
            os.remove(am.path)
            try:
                shutil.rmtree(os.path.join(
                    self.apps_path,
                    os.path.basename(am.install_path)
                ))
            except FileNotFoundError:
                # Dangling manifest
                print("{} dangling manifest has been "
                      "removed.".format(am.name))
                continue
            print("{} has been removed.".format(am.name))

    @staticmethod
    def restore(appmanifest, lib):
        """Copy game data from the archive."""
        abort_if_steam_is_running()

        installdir = os.path.basename(appmanifest.install_path)
        src = os.path.join(os.path.dirname(appmanifest.path),
                           installdir)
        dst = os.path.join(lib.install_path, installdir)
        shutil.copytree(src, dst)

# --------------------------------------------------------------------
#
# Functions
#
# --------------------------------------------------------------------
def get_archives():
    return [Archive(path) for path in PATH_ARCHIVE]


def get_libraries():
    """Steam library factory."""
    lib_paths = [get_steam_path()]
    idx_path = os.path.join(lib_paths[0], FILENAME_LIBRARY_FOLDERS)
    with open(idx_path, 'r') as f:
        dct = vdf.load(f)['LibraryFolders']

    i = 1
    while True:
        try:
            lib_paths.append(
                DiskManagement.translate_path(dct[str(i)])
            )
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
    return Steam().install_path


def get_directory_size(path):
    # Probably not the fastest implementation:
    #  - https://stackoverflow.com/q/1987119
    #  - https://stackoverflow.com/q/2485719
    dir_size = 0
    for root, dirs, files in os.walk(path):
        for basename in files:
            path = os.path.join(root, basename)
            dir_size += os.path.getsize(path)
    return dir_size


def locate_game(regex):
    libs = get_libraries()
    return [lib for lib in libs if lib.select(regex)]


def abort_if_not_archived(appmanifest):
    # TODO: This is begging to be a decorator.
    archives = get_archives()
    game = appmanifest.name

    exists = [game in archive.game_lookup for archive in archives]
    if not any(exists):
        raise RuntimeError("Game is not archived; aborting!")
    else:
        archive_idx = [i for i, x in enumerate(exists) if x][-1]
        archive = archives[archive_idx]

    archived_game = archive.select(game)[0]

    size_delta = (appmanifest.inspect_size() -
                  archive.get_archived_game_size(archived_game))

    if appmanifest != archived_game or size_delta:
        # TODO: Consider going deeper to inspect how...
        raise RuntimeError("Archived game differs; aborting!")


def abort_if_steam_is_running():
    # TODO: This is begging to be a decorator.
    if steam_is_running():
        raise RuntimeError(
            "Steam is running; probably a good idea to exit..."
        )


def steam_is_running():
    return Steam().is_running()


# --------------------------------------------------------------------
#
# Data
#
# --------------------------------------------------------------------
libs = get_libraries()

archives = get_archives()
