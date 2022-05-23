"""Disk management facades.

Provides a uniform interface for operations using disparate disk
disk management APIs available on different platforms.
"""
import os
import ntpath
from abc import ABC, abstractmethod
from collections import namedtuple

from .environment import Platform
from .fsutil import size_tool

PLATFORM = Platform.detect()
if PLATFORM == Platform.WINDOWS:
    import wmi

# --------------------------------------------------------------------
# Disk models for different platforms (used internally)
# --------------------------------------------------------------------
Disk = namedtuple('Disk', 'root, free_bytes, capacity_bytes')

class WindowsDisk(Disk):
    __slots__ = ()

    @classmethod
    def from_wmi_object(cls, wmi_object):
        free_bytes = int(wmi_object.freespace)
        capacity_bytes = int(wmi_object.size)
        root = wmi_object.caption
        return cls(
            root=root,
            free_bytes=free_bytes,
            capacity_bytes=capacity_bytes
        )


class LinuxDisk(Disk):
    __slots__ = ()

    @classmethod
    def from_path(cls, path):
        stat_result = os.statvfs(path)
        free_blocks = stat_result.f_bfree
        free_bytes = free_blocks * stat_result.f_bsize
        capacity_blocks = stat_result.f_blocks
        capacity_bytes = capacity_blocks * stat_result.f_bsize
        root = cls._find_mount_point(path)
        return cls(
            root=root,
            free_bytes=free_bytes,
            capacity_bytes=capacity_bytes
        )

    @staticmethod
    def _find_mount_point(path):
        # https://stackoverflow.com/a/4453715
        path = os.path.abspath(path)
        while not os.path.ismount(path):
            path = os.path.dirname(path)
        return path

# --------------------------------------------------------------------
# Platform-dependent disk management facade.
# --------------------------------------------------------------------
class AbstractDiskManagement(ABC):

    @abstractmethod
    def get_usage(self, path):
        """Return usage in bytes under specified path."""
        return int

    @abstractmethod
    def get_capacity(self, path):
        """Return total capacity in bytes on specified disk."""
        return int

    @abstractmethod
    def get_free_space(self, path):
        """Return free bytes on specified disk."""
        return int


class WinDiskManagement(AbstractDiskManagement):

    def get_usage(self, path):
        raise NotImplementedError("No tools supported for WSL")

    def get_capacity(self, path):
        for disk in self._enumerate_disks():
            if disk.root == self._get_drive_prefix(path):
                return int(disk.capacity_bytes)

    def get_free_space(self, path):
        for disk in self._enumerate_disks():
            if disk.root == self._get_drive_prefix(path):
                return int(disk.free_bytes)

        # No matching logical disk
        msg = f"Cannot determine containing {path}"
        raise ValueError(msg)

    @staticmethod
    def translate_path(path):
        return os.path.normpath(path)

    @staticmethod
    def _enumerate_disks():
        # Returns WindowsDisk objects
        return [
            WindowsDisk.from_wmi_object(obj)
            for obj in wmi.WMI().Win32_LogicalDisk()
            if obj.filesystem is not None
        ]

    @staticmethod
    def _get_drive_prefix(path):
        return os.path.splitdrive(path)[0].upper()


class WslDiskManagement(AbstractDiskManagement):

    def get_usage(self, path):
        return size_tool.total_size(path)

    @staticmethod
    def get_capacity(path):
        return LinuxDisk.from_path(path).capacity_bytes

    @staticmethod
    def get_free_space(path):
        return LinuxDisk.from_path(path).free_bytes

    @staticmethod
    def translate_path(path):
        drive, path = ntpath.splitdrive(path)
        relative_path = os.path.join(*path.split(ntpath.sep))
        if drive:
            # Windows path
            path = os.path.join('/', 'mnt', drive[0].lower(),
                                relative_path)
        else:
            path = relative_path

        return os.path.normpath(path)


DiskManagement = {
    Platform.WINDOWS: WinDiskManagement,
    Platform.WSL: WslDiskManagement
}[PLATFORM]
