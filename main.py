import sys

from lsb.cmd import *
from lsb.li import UUID_S, UUID_T
from lsb.connect import (
    get_adapters, get_best_adapter_idx,
    scan_for_peripherals, is_mac_in_found_peripherals,
    connect_mac, force_disconnect, cb_scan, get_mtu, my_disconnect
)
from lsb.utils import pt, cmd_dir_ans_to_dict


def connect_test(m, activate_noti=True):

    # start clean
    force_disconnect(m)

    # get internal / external adapters
    ads = get_adapters()
    ad_i = get_best_adapter_idx(ads)
    ad = ads[ad_i]

    # scan
    ad.set_callback_on_scan_found(cb_scan)
    pp = scan_for_peripherals(ad, 10000, m)

    # see mac is within scan results
    found, i = is_mac_in_found_peripherals(pp, m)
    if not found:
        sys.exit(1)

    # connect
    p = pp[i]
    if not connect_mac(p, m):
        pt('error: could not connect')
        sys.exit(1)

    # configure notification
    if activate_noti:
        p.notify(UUID_S, UUID_T, cb_rx_noti)

    # display mtu
    # get_mtu(p)

    cmd_gfv(p)
    cmd_gtm(p)
    cmd_sts(p)
    # send_cmd_arf(p)
    cmd_dir(p)

    s = 'dummy_1661451302.lid'
    z = 77950
    cmd_dwg(p, s=s)
    # cmd_dwl(p, z)
    cmd_dwf(p, z)

    cmd_crc(p, s)

    # bye, bye
    my_disconnect(p)


# ------
# main
# ------
if __name__ == "__main__":
    mac = "D0:2E:AB:D9:29:48"   # TDO bread
    connect_test(mac, activate_noti=True)
    # try:
    #     connect_test(mac, activate_noti=True)
    # except (Exception, ) as ex:
    #     pt(f'exception simpleble -> {ex}')
