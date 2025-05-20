import time

import simplepyble
import subprocess as sp
from lsb.utils import pt, linux_is_rpi, BleLsbException

g_mac_searched_for = ''
g_mac_found_in_scan = False


def cb_scan(sr):
    # sr: scan result
    # pt(f" - {sr.identifier()} [{sr.address()}]")
    global g_mac_found_in_scan
    if sr.address() == g_mac_searched_for:
        g_mac_found_in_scan = True


def get_adapters():
    ads = simplepyble.Adapter.get_adapters()
    if len(ads) == 0:
        pt('no Bluetooth adapters found')
    return ads


def get_mtu(p):
    # works so-so
    mtu = p.mtu()
    pt(f'mtu is {mtu}')


def get_best_adapter_idx(ads):
    pt('list of BLE adapters found')
    for i, ad in enumerate(ads):
        pt(f"\t- {i}: {ad.identifier()} [{ad.address()}]")
    return 0


def scan_for_peripherals(ad, timeout_ms, mac=''):
    # ad: adapter
    assert timeout_ms >= 500
    pt(f'scanning on {ad.identifier()} for {timeout_ms} ms')
    n = int(timeout_ms / 500)
    mac = mac.upper()
    global g_mac_searched_for
    global g_mac_found_in_scan
    g_mac_found_in_scan = False
    g_mac_searched_for = mac
    for i in range(n):
        ad.scan_for(500)
        if g_mac_found_in_scan:
            if ad.scan_is_active():
                ad.scan_stop()
            pt(f'\tscan early left for mac {mac}')
            break
    return ad.scan_get_results()


def is_mac_in_found_peripherals(pp, mac):
    for i, p in enumerate(pp):
        if p.address() == mac.upper():
            return True, i
    pt(f'mac {mac} not found in scan results')
    return False, -1


def connect_mac(p, mac):
    # internally, they take care of retries
    pt(f"Connecting to {mac}...")
    till = time.perf_counter() + 20
    while time.perf_counter() < till:
        try:
            p.connect()
            return True
        except (Exception, ) as ex:
            pt(f'error connect_mac -> {ex}')
            time.sleep(.1)
    raise BleLsbException('exception connect_mac')


def force_disconnect(m=''):
    m = m.upper()
    # try both variants, not care
    c = f'timeout 3 bluetoothctl disconnect'
    sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    c = f'timeout 3 bluetoothctl disconnect {m}'
    sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)


def my_disconnect(p):
    time.sleep(.1)
    p.disconnect()


def set_connection_parameters_in_linux(c_min, c_max, c_sto='250'):
    with open('/tmp/ble_c_min', 'w') as f:
        f.write(c_min)
    with open('/tmp/ble_c_max', 'w') as f:
        f.write(c_max)
    with open('/tmp/ble_c_sto', 'w') as f:
        f.write(c_sto)

    if not linux_is_rpi():
        pt('cannot do this on NOT rpi')
        return

    # todo ---> do for both hci!
    # one of these 2 orders will work
    f = '/sys/kernel/debug/bluetooth/hci0/conn_min_interval'
    sp.run(f'cp /tmp/c_min {f}', shell=True)
    f = '/sys/kernel/debug/bluetooth/hci0/conn_max_interval'
    sp.run(f'cp /tmp/c_max {f}', shell=True)
    f = '/sys/kernel/debug/bluetooth/hci0/conn_max_interval'
    sp.run(f'cp /tmp/c_max {f}', shell=True)
    f = '/sys/kernel/debug/bluetooth/hci0/conn_min_interval'
    sp.run(f'cp /tmp/c_min {f}', shell=True)
    f = '/sys/kernel/debug/bluetooth/hci0/supervision_timeout'
    sp.run(f'cp /tmp/c_sto {f}', shell=True)
