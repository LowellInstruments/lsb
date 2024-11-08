import json
import math
import time
from datetime import datetime, timezone
from re import findall
from lsb.li import UUID_S, UUID_R
from lsb.utils import (
    pt, cmd_dir_ans_to_dict, GPS_FRM_STR,
    print_dwf_progress, print_dwl_progress
)


rx = bytes()
g_cmd = bytes()
g_dwf_z = 0
g_dwf_i = 0
i = 0


def get_rx():
    return rx


def cb_rx_noti(data):
    global rx
    rx += data
    if g_cmd == b'DWF':
        global g_dwf_i
        g_dwf_i += 1
        print_dwf_progress(g_dwf_i, len(rx), g_dwf_z)
    # if g_cmd not in (b'DWL', b'DWF', b'DIR'):
        # pt(f'-> {rx}')


def _cmd(p, cmd, i=None, z=None, timeout=3, empty=True, verbose=False):
    def ans_done():
        tag = cmd.decode()[:3]
        d = {
            # todo ---> complete some of these conditions
            '__A': lambda: rx and rx.endswith(b'\x04\n\r'),
            '__B': lambda: rx and rx.startswith(b'__B') and len(rx) == 38,
            'ARF': lambda: rx and rx.startswith(b'ARF 020'),
            'BAT': lambda: rx and rx.startswith(b'BAT') and len(rx) == 10,
            'CFG': lambda: rx == b'CFG 00',
            'CRC': lambda: rx and rx.startswith(b'CRC') and len(rx) == 14,
            'DEL': lambda: rx == b'DEL 00',
            'DIR': lambda: rx and rx.endswith(b'\x04\n\r'),
            'DWL': lambda: rx and len(rx) == (i + 1) * 2048 or rx and len(rx) == z,
            'DWG': lambda: rx == b'DWG 00',
            'DWF': lambda: rx and len(rx) == z,
            'FRM': lambda: rx == b'FRM 00',
            'GDO': lambda: rx and rx.startswith(b'GDO') and len(rx) == 18,
            'GDX': lambda: rx and len(findall(r"[-+]?(?:\d*\.*\d+)", rx.decode())) == 3,
            'GFV': lambda: rx and rx.startswith(b'GFV 0'),
            'GTM': lambda: rx and rx.startswith(b'GTM'),
            'GSP': lambda: rx and rx.startswith(b'GSP') and len(rx) == 10,
            'GST': lambda: rx and rx.startswith(b'GST') and len(rx) == 10,
            'LOG': lambda: rx and rx.startswith(b'LOG') and len(rx) == 8,
            'RWS': lambda: rx == b'RWS 00',
            'SCC': lambda: rx == b'SCC 00',
            'STM': lambda: rx == b'STM 00',
            'STS': lambda: rx and rx.startswith(b'STS 020'),
            'SWS': lambda: rx == b'SWS 00',
            'UTM': lambda: rx and rx.startswith(b'UTM 0'),
            'WAK': lambda: rx and rx.startswith(b'WAK') and len(rx) == 8,
            'XOD': lambda: rx and rx.endswith(b'.LIX')
        }
        return d[tag]()

    def _wait_ans_done():
        till = time.perf_counter() + timeout
        while time.perf_counter() < till:
            if ans_done():
                # pt(f'\nfast ans for cmd {cmd}')
                return rx
        pt(f'\nans BAD for cmd {cmd} -> rx {rx}')

    global rx
    if empty:
        rx = bytes()
    cmd = cmd if type(cmd) is bytes else cmd.encode()
    global g_cmd
    g_cmd = cmd[:3]
    if verbose:
        pt(f'\n<- {cmd}')
    p.write_request(UUID_S, UUID_R, cmd)
    rv = _wait_ans_done()
    # pt('len(rx)', len(rx))
    return rv


def cmd_arf(p):
    # ARA: adjust advertisement rate
    # ARF: adjust advertisement fast rate
    # ARA ARF
    #  0   0 - no adjust, set as slow forever
    #  0   1 = no adjust, set as fast forever
    #  1   X - ignore ARF, fast forever
    return _cmd(p, 'ARF \r')


def cmd_bat(p):
    rv = _cmd(p, 'BAT \r')
    ok = rv and len(rv) == 10 and rv.startswith(b'BAT')
    if not ok:
        return
    a = rv
    if a and len(a.split()) == 2:
        # a: b'BAT 04BD08'
        _ = a.split()[1].decode()
        b = _[-2:] + _[-4:-2]
        b = int(b, 16)
        return b


def cmd_beh(p, rvn=4, tts=0, spc=1, fow=0, nms=0, owb=0):
    cmds = (
        f'BEH 04RVN{rvn}\r',
        f'BEH 04TTS{tts}\r',
        f'BEH 04SPC{spc}\r',
        f'BEH 04FOW{fow}\r',
        f'BEH 04NMS{nms}\r',
        f'BEH 04OWB{owb}\r',
    )
    cond = "rx.startswith(b'BEH 06')"
    for c in cmds:
        _cmd(p, c, cond)
        time.sleep(.1)


def cmd_crc(p, s):
    cmd = 'CRC {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=60)


def cmd_dda(p, g):
    lat, lon, _, __ = g
    lat = GPS_FRM_STR.format(float(lat))
    lon = GPS_FRM_STR.format(float(lon))
    s = f'{lat} {lon}'
    c = '__A {:02x}{}\r'.format(len(str(s)), s)
    ls_b = _cmd(p, c, timeout=30)
    if not ls_b:
        # this is an error
        return
    ls = cmd_dir_ans_to_dict(ls_b)
    # this might be populated or not
    pt(f'\tls {ls}')
    return {'ls': ls}


def cmd_ddb(p, rerun):
    # time() -> seconds since epoch, in UTC
    rerun = int(rerun)
    dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
    s = f"{rerun}{dt.strftime('%Y/%m/%d %H:%M:%S')}"
    c = '__B {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, c, timeout=30)


def cmd_del(p, s):
    cmd = 'DEL {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=3)


def cmd_dir(p):
    ls_b = _cmd(p, 'DIR \r', timeout=10)
    if not ls_b:
        # this is an error
        return
    ls = cmd_dir_ans_to_dict(ls_b)
    # pt(f'\tls {ls}')
    # this might be populated or not
    return {'ls': ls}


def cmd_dwl(p, z, ip=None, port=None):
    # z: file size
    n = math.ceil(z / 2048)
    print_dwl_progress(0, z)

    # need to clean the first one
    global rx
    rx = bytes()
    t = time.perf_counter()
    for i in range(n):
        cmd = 'DWL {:02x}{}\r'.format(len(str(i)), i)
        _cmd(p, cmd, i=i, z=z, empty=False)
        print_dwl_progress(len(rx), z)
        pt(f'chunk #{i} len {len(rx)}')

    if len(rx) == z:
        return rx


def cmd_dwf(p, z, ip=None, port=None):
    # z: file size
    # ble_mat_progress_dl(0, z, ip, port)

    # need to clean the first one
    global rx
    rx = bytes()
    cmd = 'DWF \r'
    global g_dwf_z
    global g_dwf_i
    g_dwf_z = z
    g_dwf_i = 0
    # consider at least 5 KB/s for DWF
    calc_timeout = math.ceil(z / 5000)
    calc_timeout += 10
    _cmd(p, cmd, i=None, z=z, timeout=calc_timeout)
    if len(rx) == z:
        return rx


def cmd_dwg(p, s):
    cmd = 'DWG {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=3)


def cmd_frm(p):
    return _cmd(p, 'FRM \r')


def cmd_gfv(p):
    return _cmd(p, 'GFV \r')


def cmd_gtm(p):
    return _cmd(p, 'GTM \r')


def cmd_gsp(vp):
    # Get Sensor Pressure
    rv = _cmd(vp, 'GSP \r')
    # rv: GSP 04ABCD
    if rv and len(rv.split()) == 2:
        # a: b'GSP 043412'
        _ = rv.split()[1].decode()
        vp = _[2:6]
        # p: '3412' --> '1234'
        vp = vp[-2:] + vp[:2]
        vp = int(vp, 16)
        return vp


def cmd_gst(p):
    # gst: Get Sensor Temperature
    rv = _cmd(p, 'GST \r')
    # rv: b'GST 043412'
    if rv and len(rv.split()) == 2:
        _ = rv.split()[1].decode()
        vt = _[2:6]
        # t: '3412' --> '1234'
        vt = vt[-2:] + vt[:2]
        vt = int(vt, 16)
        return vt


def cmd_rws(p, g):
    # RUN with STRING
    lat, lon, _, __ = g
    lat = GPS_FRM_STR.format(float(lat))
    lon = GPS_FRM_STR.format(float(lon))
    s = f'{lat} {lon}'
    cmd = 'RWS {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=60)


def cmd_rst(p):
    return _cmd(p, 'RST \r', timeout=2)


def cmd_stm(p):
    # time() -> seconds since epoch, in UTC
    dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
    s = dt.strftime('%Y/%m/%d %H:%M:%S')
    cmd = 'STM {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd)


def cmd_sts(p):
    return _cmd(p, 'STS \r')


def cmd_sws(p, g):
    # STOP with STRING
    lat, lon, _, __ = g
    lat = GPS_FRM_STR.format(float(lat))
    lon = GPS_FRM_STR.format(float(lon))
    s = f'{lat} {lon}'
    cmd = 'SWS {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd, timeout=60)


def cmd_utm(p):
    return _cmd(p, 'UTM \r')


def cmd_wak(p, s):
    # (de-)activate Wake mode
    assert s in ('on', 'off')
    rv = _cmd(p, 'WAK \r')
    if s == 'off' and rv == b'WAK 0200':
        return 1
    if s == 'on' and rv == b'WAK 0201':
        return 1
    # just toggle again :)
    time.sleep(.1)
    rv = _cmd(p, 'WAK \r')
    if s == 'off' and rv == b'WAK 0200':
        return 1
    if s == 'on' and rv == b'WAK 0201':
        return 1


def cmd_log(p):
    # (de-)activate log serial output
    return _cmd(p, 'LOG \r')


def cmd_xod(p):
    return _cmd(p, 'XOD \r')


def cmd_cfg(p, cfg_d):
    assert type(cfg_d) is dict
    s = json.dumps(cfg_d)
    cmd = 'CFG {:02x}{}\r'.format(len(str(s)), s)
    return _cmd(p, cmd)


def cmd_gdo(p):
    rv = _cmd(p, 'GDO \r')
    if not rv:
        return
    if rv and len(rv.split()) == 2:
        # a: b'GDO 0c112233445566'
        _ = rv.split()[1].decode()
        dos, dop, dot = _[2:6], _[6:10], _[10:14]
        dos = dos[-2:] + dos[:2]
        dop = dop[-2:] + dop[:2]
        dot = dot[-2:] + dot[:2]
        if dos.isnumeric():
            return dos, dop, dot


def cmd_gdx(p):
    rv = _cmd(p, 'GDX \r')
    # rv: b'GDX -0.03, -0.41, 17.30'
    if not rv:
        return
    a = rv[4:].decode().replace(' ', '').split(',')
    if a and len(a) == 3:
        dos, dop, dot = a
        return dos, dop, dot


def cmd_scc(p, tag, v):
    assert len(tag) == 3
    assert len(v) == 5
    tag = tag.upper()
    cmd = f'SCC 08{tag}{v}\r'
    return _cmd(p, cmd, timeout=10)
