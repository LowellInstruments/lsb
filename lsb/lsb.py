import simplepyble

from lsb.utils import _p


def get_adapters():
    ads = simplepyble.Adapter.get_adapters()
    if len(ads) == 0:
        _p('no Bluetooth adapters found')
    return len(ads)


def get_best_adapter_idx(ads):
    for i, ad in enumerate(ads):
        print(f"{i}: {ad.identifier()} [{ad.address()}]")
        print(ad)
    # todo --> change this
    return 0


def scan_for_peripherals(ad, timeout_ms):
    # ad: adapter
    ad.scan_for(timeout_ms)
    return ad.scan_get_results()


def is_mac_in_found_peripherals(pp, mac):
    for i, p in enumerate(pp):
        if pp.address().lower() == mac.lower():
            return True, i
    return False, -1


def connect_mac(p, mac):
    _p(f"Connecting to {mac}...")
    try:
        p.connect()
        return True
    except (Exception, ) as ex:
        _p(f'error connect_mac -> {ex}')


def get_services(p):
    _p("listing services...")
    try:
        services = p.services()
        service_characteristic_pair = []
        for service in services:
            for characteristic in service.characteristics():
                service_characteristic_pair.append((service.uuid(), characteristic.uuid()))
        return service_characteristic_pair
    except (Exception, ) as ex:
        _p(f'error listing services -> {ex}')
