"""Test Cases for the Steam Module."""
import os
import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from ..facades import disks

from ..steam import Library, AppManifest

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

class TestAppManifest(unittest.TestCase):

    def setUp(self):
        self.sut = AppManifest(os.path.join(DATA_DIR, 'appmanifest_379720.acf'))

    def test___iter__(self):
        """__iter__ is overriden to support conversion to a dict."""

        expected_data = {
            'id':379720,
            'name': "DOOM",
            'manifest_path': os.path.join(DATA_DIR, 'appmanifest_379720.acf'),
            'install_path': os.path.join(DATA_DIR, 'common', 'DOOM'),
            'size': 73756206574
        }

        self.assertEqual(dict(self.sut), expected_data)


class TestLibrary(unittest.TestCase):

    def setup_mock_disks_facade(self):
        self.mock_disk_manager = MagicMock(spec=disks.AbstractDiskManagement)
        self.mock_disk_manager.get_free_space.return_value = 5807849472
        return self.mock_disk_manager

    def setup_mock_games(self):
        self.mock_games = {
            'game1': MagicMock(spec=AppManifest, size=330000),
            'game2': MagicMock(spec=AppManifest, size=324789)
        }

    def setUp(self):
        self.sut = Library('C:/SteamLibrary')
        self.sut.disk_management = self.setup_mock_disks_facade()
        self.setup_mock_games()

    def test_disk_management(self):
        """Property is a concrete disk management facade.

        We don't care about the platform, we assume that's handled
        properly by the facades sub-pacakage.
        """
        self.assertIsInstance(self.sut.disk_management,
                disks.AbstractDiskManagement)

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

        # Set up the properties this property uses; the facade to get
        # disk space used and the location of game installations.
        dummy_install_path = 'C:/SteamLibrary/steamapps/common'
        stub_install_path_property.return_value = dummy_install_path

        self.assertEqual(self.sut.free, '5.8 GB')
        self.mock_disk_manager.get_free_space.assert_called_with(
            dummy_install_path)

    @patch.object(Library, 'games', new_callable=PropertyMock)
    def test___iter__(self, mock_games_property):
        """__iter__ is overriden to support conversion to a dict."""
        mock_games_property.return_value = self.mock_games
        expected = {
            'path': 'C:/SteamLibrary',
            'install_path': 'C:/SteamLibrary/steamapps/common',
            'apps_path': 'C:/SteamLibrary/steamapps',
            'size': 654789,
            'free_bytes': self.mock_disk_manager.get_free_space()
        }

        self.assertEqual(dict(self.sut), expected)


if __name__ == '__main__':
    unittest.main()