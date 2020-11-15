"""Toggle desktop resolution."""

# This is a quick hack - the specific registry key will differ as I
# found out later when this stopped working. Obviously the resolution
# switching between UW and HD is also ultra specific. The reason for
# the hack is to implement it as a Steam executable "game" so that I
# can toggle desktop resolution via the Steam Link - some games don't
# play nice with the host res differing from the target monitor res.
# Basically, they are a bit too clever about it and fall over,
# screwing up aspect ratio etc.


import os
import winreg


APP_INSTALL = os.path.join(os.environ['USERPROFILE'], 'apps',
                           'monitorswitcher')


def get_xresolution():
    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        (r'SYSTEM\CurrentControlSet\Hardware Profiles\UnitedVideo\CONTROL\VIDEO\{6CF520FF-2974-11E8-9E3A-C32D69779901}\0000'),
        winreg.KEY_QUERY_VALUE
    )

    value_typeflag = winreg.QueryValueEx(
        key,
        'DefaultSettings.XResolution'
    )

    return value_typeflag[0]


if __name__ == '__main__':

    switch = {
        3440: 'HD.xml',
        1920: 'UW.xml'
    }

    os.chdir(APP_INSTALL)
    os.system(' '.join(['MonitorSwitcher.exe',
               '-load:{}'.format(switch[get_xresolution()])]))
