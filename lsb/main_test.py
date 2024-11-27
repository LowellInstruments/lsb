import simplepyble

ads = simplepyble.Adapter.get_adapters()
ad = ads[0]

while 1:
    ad.scan_for(5000)
    ls_per = ad.scan_get_results()
    print(len(ls_per))

