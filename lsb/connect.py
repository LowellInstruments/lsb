import time

import simplepyble
import subprocess as sp
from lsb.utils import pt


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
        pt(f"  - {i}: {ad.identifier()} [{ad.address()}]")
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
            pt(f'scan early left for mac {mac}')
            break
    return ad.scan_get_results()


def is_mac_in_found_peripherals(pp, mac):
    for i, p in enumerate(pp):
        if p.address() == mac.upper():
            return True, i
    pt(f'mac {mac} not found in scan results')
    return False, -1


def connect_mac(p, mac):
    pt(f"Connecting to {mac}...")
    try:
        p.connect()
        return True
    except (Exception, ) as ex:
        pt(f'error connect_mac -> {ex}')


def get_services(p):
    pt("listing services...")
    try:
        services = p.services()
        service_characteristic_pair = []
        for service in services:
            for characteristic in service.characteristics():
                service_characteristic_pair.append((service.uuid(), characteristic.uuid()))
        return service_characteristic_pair
    except (Exception, ) as ex:
        pt(f'error listing services -> {ex}')


def force_disconnect(m=''):
    m = m.upper()
    c = f'bluetoothctl disconnect {m}'
    sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)


def my_disconnect(p):
    time.sleep(1)
    p.disconnect()
