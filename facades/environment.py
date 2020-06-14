import platform
from enum import Enum


class Platform(Enum):
    WINDOWS = 1
    WSL = 2
    LINUX = 3

    @classmethod
    def detect(cls):
        """Return an unambiguous platform identifier.

        Parameters
        ----------

        n/a


        Returns
        -------

        Platform
            Unambiguous enum value indicating the run environment.


        Raises
        ------

        RuntimeError
            Detected platform is not recognised

        NotImplementedError
            Support not yet implemented for the detected platform
        """
        platform_system = platform.system()
        if platform_system == 'Windows':
            this_platform = cls.WINDOWS

        elif platform_system == 'Linux':
            if 'Microsoft' in platform.release():
                this_platform = cls.WSL

            else:
                this_platform = cls.LINUX
                msg = "Linux is currently not a supported platform"
                raise NotImplementedError(msg)

        else:
            msg = f"{platform_system} is not a recognised platform"
            raise RuntimeError(msg)

        return this_platform