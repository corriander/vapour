"""Test Cases for the Steam Module."""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from ..facades.disks import AbstractDiskManagement
from ..facades import disks

from ..steam import Library


class TestLibrary(unittest.TestCase):

    def setUp(self):
        self.sut = Library('C:/SteamLibrary')

    def test_disk_management(self):
        """Property is a concrete disk management facade.

        We don't care about the platform, we assume that's handled
        properly by the facades sub-pacakage.
        """
        self.assertIsInstance(self.sut.disk_management,
                AbstractDiskManagement)

    @patch.object(Library, 'install_path', new_callable=PropertyMock)
    def test_free(self, stub_install_path_property):
        """Property wraps a facade method to get free space available.

        Steam libraries exist on disks/partitions, with that
        partition's free space being the space available for the lib.
        Interaction with disk management is hidden behind a facade to
        allow multi-platform usage. This property takes the retval of
        that facade's method and transforms it to a human readable
        string.
        """
        mock_facade = MagicMock(spec=AbstractDiskManagement)
        mock_facade.get_free_space.return_value = 5807849472

        # Set up the properties this property uses; the facade to get
        # disk space used and the location of game installations.
        self.sut.disk_management = mock_facade
        dummy_install_path = 'C:/SteamLibrary/steamapps/common'
        stub_install_path_property.return_value = dummy_install_path

        self.assertEqual(self.sut.free, '5.8 GB')


if __name__ == '__main__':
    unittest.main()