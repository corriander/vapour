"""Toggle Resolution."""

import os
import winreg


APP_INSTALL = os.path.join(os.environ['USERPROFILE'], 'apps',
                           'monitorswitcher')


def get_xresolution():
    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        (r'SYSTEM\CurrentControlSet\Hardware Profiles\UnitedVideo\CONTROL\VIDEO\{48150032-5642-401B-97CF-5C845BFF31AE}\0000'),
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
