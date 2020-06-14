"""Disk management facades.

Provides a uniform interface for operations using disparate disk
disk management APIs available on different platforms.
"""
import os
from abc import ABC, abstractmethod
from collections import namedtuple

from .environment import Platform

PLATFORM = Platform.detect()
if PLATFORM == Platform.WINDOWS:
    import wmi

# --------------------------------------------------------------------
# Disk models for different platforms (used internally)
# --------------------------------------------------------------------
Disk = namedtuple('Disk', 'root, free_bytes')

class WindowsDisk(Disk):
    __slots__ = ()

    @classmethod
    def from_wmi_object(cls, wmi_object):
        free_bytes = int(wmi_object.freespace)
        root = wmi_object.caption
        return cls(root=root, free_bytes=free_bytes)


class LinuxDisk(Disk):
    __slots__ = ()

    @classmethod
    def from_path(cls, path):
        stat_result = os.statvfs(path)
        free_blocks = stat_result.f_bfree
        free_bytes = free_blocks * stat_result.f_bsize
        root = cls._find_mount_point(path)
        return cls(root=root, free_bytes=free_bytes)

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
    def get_free_space(self, path):
        """Return free bytes on specified disk."""
        return int


class WinDiskManagement(AbstractDiskManagement):

    def get_free_space(self, path):
        for disk in self._enumerate_disks():
            if disk.root == self._get_drive_prefix(path):
                return int(disk.free_bytes)

        # No matching logical disk
        msg = f"Cannot determine containing {path}"
        raise ValueError(msg)

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

    def get_free_space(self, path):
        return LinuxDisk.from_path(path).free_bytes


DiskManagement = {
    Platform.WINDOWS: WinDiskManagement,
    Platform.WSL: WslDiskManagement
}[PLATFORM]