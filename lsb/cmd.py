import math
import time

from lsb.li import UUID_S, UUID_R
from lsb.utils import pt, cmd_dir_ans_to_dict

rx = bytes()


g_cmd = bytes()


def cb_rx_noti(data):
    global rx
    rx += data
    if g_cmd not in (b'DWL', b'DWF'):
        pt(f'-> {rx}')


def _cmd(p, cmd, i=None, z=None, timeout=3, empty=True):
    def ans_done():
        tag = cmd.decode()[:3]
        d = {
            'ARF': lambda: rx and rx.startswith(b'ARF 020'),
            'CRC': lambda: rx and rx.startswith(b'CRC') and len(rx) == 14,
            'DIR': lambda: rx and rx.endswith(b'\x04\n\r'),
            'DWL': lambda: rx and len(rx) == (i + 1) * 2048 or \
                           rx and len(rx) == z,
            'DWG': lambda: rx and rx == b'DWG 00',
            'DWF': lambda: rx and len(rx) == z,
            'STS': lambda: rx and rx.startswith(b'STS 020'),
        }
        return d[tag]()

    def _wait_ans_done():
        till = time.perf_counter() + timeout
        try:
            while time.perf_counter() < till:
                if ans_done():
                    pt(f'\nfast ans for cmd {cmd}')
                    return rx
            pt(f'\nans BAD for cmd {cmd} -> rx {rx}')
        except (Exception, ) as ex:
            pt(f'\nexception while send_cmd -> {ex}')

    global rx
    if empty:
        rx = bytes()
    cmd = cmd if type(cmd) is bytes else cmd.encode()
    global g_cmd
    g_cmd = cmd[:3]
    pt(f'<- {cmd}')
    p.write_request(UUID_S, UUID_R, cmd)
    rv = _wait_ans_done()
    print('len(rx)', len(rx))
    return rv


def cmd_beh(p, rvn=4, tts=0, cpt=1, fow=0, nms=0, owb=0):
    cmds = (
        f'BEH 04RVN{rvn}\r',
        f'BEH 04TTS{tts}\r',
        f'BEH 04CPT{cpt}\r',
        f'BEH 04FOW{fow}\r',
        f'BEH 04NMS{nms}\r',
        f'BEH 04OWB{owb}\r',
    )
    cond = "rx.startswith(b'BEH 06')"
    for c in cmds:
        _cmd(p, c, cond)
        time.sleep(.1)


def cmd_arf(p):
    # ARA: adjust advertisement rate
    # ARF: adjust advertisement fast rate
    # ARA ARF
    #  0   0 - no adjust, set as slow forever
    #  0   1 = no adjust, set as fast forever
    #  1   X - ignore ARF, fast forever
    return _cmd(p, 'ARF \r')


def cmd_sts(p):
    return _cmd(p, 'STS \r')


def cmd_dir(p):
    ls_b = _cmd(p, 'DIR \r', timeout=10)
    ls = cmd_dir_ans_to_dict(ls_b)
    pt(f'dir ls {ls}')
    return ls


def cmd_dwl(p, z, ip=None, port=None) -> tuple:
    # z: file size
    n = math.ceil(z / 2048)
    # ble_mat_progress_dl(0, z, ip, port)

    # need to clean the first one
    global rx
    rx = bytes()
    t = time.perf_counter()
    for i in range(n):
        cmd = 'DWL {:02x}{}\r'.format(len(str(i)), i)
        _cmd(p, cmd, i=i, z=z, empty=False)
        # ble_mat_progress_dl(len(self.ans), z, ip, port)
        # print('chunk #{} len {}'.format(i, len(self.ans)))

    t = time.perf_counter() - t
    print(f'speed {(z / t)/ 1000} KBps')
    rv = 0 if z == len(rx) else 1
    return rv, rx


def cmd_dwf(p, z, ip=None, port=None) -> tuple:
    # z: file size
    # ble_mat_progress_dl(0, z, ip, port)

    # need to clean the first one
    global rx
    rx = bytes()
    t = time.perf_counter()

    cmd = 'DWF \r'
    _cmd(p, cmd, i=None, z=z, timeout=60)

    t = time.perf_counter() - t
    print(f'speed {(z / t) / 1000} KBps')
    rv = 0 if z == len(rx) else 1
    return rv, rx


def cmd_dwg(p, s):
    cmd = 'DWG {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=3)


def cmd_crc(p, s):
    cmd = 'CRC {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=60)

