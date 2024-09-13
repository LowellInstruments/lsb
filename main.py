import sys
import time
from lsb.lsb import (
    get_adapters, get_best_adapter_idx,
    scan_for_peripherals, is_mac_in_found_peripherals,
    connect_mac, get_services
)
from lsb.utils import _p


# let's hardcode them for now
UUID_T = 'f0001132-0451-4000-b000-000000000000'
UUID_R = 'f0001131-0451-4000-b000-000000000000'
UUID_S = 'f0001130-0451-4000-b000-000000000000'


rx = bytes()


def cb_rx_noti(data):
    global rx
    rx += data
    print(f'-> {rx}')


def send_cmd(p, cmd, ans_done_cond, timeout=3):
    def _ans_done():
        till = time.perf_counter() + timeout
        while time.perf_counter() < till:
            if eval(ans_done_cond):
                _p(f'ans done for cmd {cmd}')
                return True
    global rx
    rx = bytes()
    _p(f'<- {cmd}')
    p.write_request(UUID_S, UUID_T, cmd)
    return _ans_done()


def connect_test(m):

    # get internal / external adapters
    ads = get_adapters()
    ad_i = get_best_adapter_idx(ads)
    ad = ads[ad_i]

    # scan
    ad.set_callback_on_scan_found(
        lambda x: _p(f"    found - {x.identifier()} [{x.address()}]"))
    pp = scan_for_peripherals(ad, 5000)

    # see mac is within scan results
    found, i = is_mac_in_found_peripherals(pp, m)
    if not found:
        _p('error: mac not found in scan results')
        sys.exit(1)

    # connect
    p = pp[i]
    if not connect_mac(m, p):
        _p('error: could not connect')
        sys.exit(1)
    if not get_services(p):
        _p('error: could not get services')
        sys.exit(1)

    # display mtu
    mtu = p.get_mtu()
    _p(f'mtu is {mtu}')

    # configure notification
    # todo ---> might be like this or the other way around UUID_T / UUID_R
    rv = p.notify(UUID_S, UUID_R, cb_rx_noti)
    _p(f'rv set notify: {rv}')

    # write command
    cmd = b'STS \r'
    cond = "rx.startswith(b'STS 0')"
    send_cmd(p, cmd, cond)

    # bye, bye
    time.sleep(3)
    p.disconnect()


if __name__ == "__main__":
    mac = '11:22:33:44:55:66'
    connect_test(mac)
