import simplepyble

ads = simplepyble.Adapter.get_adapters()
ad = ads[0]

if __name__ == '__main__':
    print('scanning')
    while 1:
        ad.scan_for(500)
        ls_per = ad.scan_get_results()
        for p in ls_per:
            if 'D0:2E:AB:D9:29:48' in p.address():
                print(p.address(), p.identifier())

