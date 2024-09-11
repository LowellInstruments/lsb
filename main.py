import sys
import time
from lsb.lsb import (
    get_adapters, get_best_adapter_idx,
    scan_for_peripherals, is_mac_in_found_peripherals, connect_mac, get_services
)
from lsb.utils import _p


if __name__ == "__main__":
    ads = get_adapters()
    ad_i = get_best_adapter_idx(ads)
    ad = ads[ad_i]

    # scan
    ad.set_callback_on_scan_found(
        lambda p: _p(f"    found - {p.identifier()} [{p.address()}]"))
    pp = scan_for_peripherals(ad, 5000)
    mac = '11:22:33:44:55:66'
    found, i = is_mac_in_found_peripherals(pp, mac)
    if not found:
        sys.exit(1)
    p = pp[i]

    # connect
    if not connect_mac(mac, p):
        sys.exit(1)
    if not get_services(p):
        sys.exit(1)

    # let's hardcode them for now
    # todo ---> check this are ok
    UUID_T = 'f0001132-0451-4000-b000-000000000000'
    UUID_R = 'f0001131-0451-4000-b000-000000000000'
    UUID_S = 'f0001130-0451-4000-b000-000000000000'

    # configure notification
    # todo ---> might be like this or the other way around UUID_T / UUID_R
    rv = p.notify(UUID_S, UUID_R, lambda data: _p(f"Notification: {data}"))
    _p(f'rv notify: {rv}')

    # write command
    cmd = b'STS \r'
    p.write_request(UUID_S, UUID_T, cmd)

    time.sleep(3)
    p.disconnect()
