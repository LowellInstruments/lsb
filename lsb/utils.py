import socket
import subprocess as sp


GPS_FRM_STR = '{:+.6f}'
DDH_GUI_UDP_PORT = 12349
STATE_DDS_BLE_DOWNLOAD_PROGRESS = 'state_dds_ble_download_progress'
_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)



class BleLsbException(Exception):
    pass


def pt(s):
    return print(s)


def cmd_dir_ans_to_dict(ls, ext='*', match=True):
    if ls is None:
        return {}

    if b'ERR' in ls:
        return b'ERR'

    if type(ext) is str:
        ext = ext.encode()

    files, idx = {}, 0

    # ls: b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r\n\rMAT.cfg\t\t\t189\n\r\x04\n\r'
    ls = ls.replace(b'System Volume Information\t\t\t0\n\r', b'')
    ls = ls.split()

    while idx < len(ls):
        name = ls[idx]
        if name in [b'\x04']:
            break

        names_to_omit = (
            b'.',
            b'..',
        )

        if type(ext) is str:
            ext = ext.encode()
        # wild-card case
        if ext == b'*' and name not in names_to_omit:
            files[name.decode()] = int(ls[idx + 1])
        # specific extension case
        elif name.endswith(ext) == match and name not in names_to_omit:
            files[name.decode()] = int(ls[idx + 1])
        idx += 2
    return files


def linux_is_rpi():
    c = 'cat /proc/cpuinfo | grep aspberry'
    rv = sp.run(c, shell=True)
    return rv.returncode == 0


def print_dwl_progress(n, z):
    x = int((n / z) * 100)
    pt(f'{x} %')
    _ = '{}/{}'.format(STATE_DDS_BLE_DOWNLOAD_PROGRESS, x)
    _sk.sendto(_.encode(), ('127.0.0.1', 12749))


def print_dwf_progress(i, n, z, do_it=True):
    if not do_it:
        return
    if (i % 10) == 0:
        print_dwl_progress(n, z)
