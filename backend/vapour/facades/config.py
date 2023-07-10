import json
import os

from .environment import Platform


if Platform.detect() == Platform.WINDOWS:
    import winreg

    class XDG(object):
        XDG_CONFIG_HOME = os.path.normpath(os.path.expanduser('~/AppData/Local'))

    xdg = XDG

else:
    import xdg  # Incompatibility with python versions used by WMI


class Settings(object):
    path = os.path.join(xdg.XDG_CONFIG_HOME, 'vapour', 'settings.json')

    def __init__(self):
        with open(self.path) as f:
            self._data = json.load(f)

    @property
    def apps_config(self):
        """Dictionary of configuration for specific apps.

        Configuration elements relate to App classes.
        """
        try:
            return self._data['apps']
        except KeyError:
            return {}

    @property
    def collections(self):
        """Dictionary describing library configuration."""
        try:
            return self._data['collections']
        except KeyError:
            return []

    @property
    def system(self):
        """Dictionary describing system configuration."""
        try:
            return self._data['system']
        except KeyError:
            return dict()


class ConfigMixin(object):
    settings = Settings()

    @property
    def config(self) -> dict:
        """Dictionary of app-specific settings.

        Contains things like hardcoded installation paths, etc.
        """
        config = self.settings.apps_config
        return config.get(self.__class__.__name__, {})
