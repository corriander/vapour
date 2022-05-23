"""Facades for interacting with Programs"""
import getpass
import subprocess
import os
from abc import ABC, abstractmethod

import psutil # NOTE: multi-platform but not used here for wsl

from .config import ConfigMixin
from .environment import Platform

PLATFORM = Platform.detect()
if PLATFORM == Platform.WINDOWS:
    import winreg

# --------------------------------------------------------------------
# Operating System contexts
# --------------------------------------------------------------------
class AbstractOperatingSystemContext(ABC):
    """Abstract base type for modelling the OS context.

    If this tool is running in WSL, the context is Windows, not the
    distro instance we're inside. If Windows, the context is Windows.
    """

    @abstractmethod
    def running_processes(self):
        """Set of names of running processes."""
        return list(str)

    @property
    def user(self):
        return getpass.getuser()

class WslContext(AbstractOperatingSystemContext):

    def running_processes(self):
        return (
            self._running_processes_winhost().union(
                self._running_processes_internal()
            )
        )

    def _running_processes_winhost(self):
        cmd = "tasklist.exe | awk '{print $1}'"
        bytes_out = subprocess.check_output(cmd, shell=True)
        return set(bytes_out.decode('utf8').splitlines())

    def _running_processes_internal(self):
        cmd = ['ps', '-o', 'cmd=', '-u', self.user]
        bytes_out = subprocess.check_output(cmd, shell=False)
        return set(bytes_out.decode('utf8').splitlines())


class WindowsContext(AbstractOperatingSystemContext):

    def running_processes(self):
        return set([ps.name() for ps in psutil.process_iter()])


# --------------------------------------------------------------------
# Supported Apps
# --------------------------------------------------------------------
class App(ABC, ConfigMixin):

    @property
    def install_path(self):
        return self._install_path

    @property
    def os_context(self):
        try:
            return self._os_context
        except AttributeError:
            self._os_context = OperatingSystemContext()
            return self._os_context

    def is_running(self, case_sensitive=True):
        this_process = self.process_name
        process_names = self.os_context.running_processes()

        if not case_sensitive:
            this_process = this_process.lower()
            process_names = set([
                name.lower()
                for name in process_names
            ])

        return this_process in process_names


class WindowsApp(App):

    def is_running(self, case_sensitive=False):
        return super().is_running(case_sensitive=case_sensitive)


class Steam(WindowsApp):

    REGISTRY_KEY = r'SOFTWARE\Valve\Steam'
    REGISTRY_KEY_INSTALL_PATH = 'SteamPath'

    process_name = 'steam.exe'

    @property
    def install_path(self):
        try:
            return super().install_path

        except AttributeError:
            try:
                # Derive it from the windows registry
                path = self._get_install_path_from_winreg()

            except RuntimeError as e:
                # Looks like we can't, fetch it from config
                try:
                    path = self.config['install-path']
                except Exception as e_inner:
                    raise e

            self._install_path = path
            return path


    def _get_install_path_from_winreg(self):
        try:
            key = winreg.HKEY_CURRENT_USER
        except NameError:
            msg = "Cannot detect steam path; configure manually"
            raise RuntimeError(msg)

        subkey = self.REGISTRY_KEY
        access_flag = winreg.KEY_QUERY_VALUE

        steam_key = winreg.OpenKey(key, subkey, access=access_flag)
        value_typeflag = winreg.QueryValueEx(
            steam_key,
            self.REGISTRY_KEY_INSTALL_PATH
        )
        return os.path.normpath(value_typeflag[0])


OperatingSystemContext = {
    Platform.WSL: WslContext,
    Platform.WINDOWS: WindowsContext
}[PLATFORM]