#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from dateutil.parser import parse
from collections import OrderedDict

def main(argv):
    accounts_data=[]
    for arg in argv:
        accounts_data.insert(1, (float(arg), next(argv)))

    data = []
    for s in sys.stdin:
        rec = s.split()
        if len(rec) != 4:
            raise ValueError('Data from scale not correct: ' + rec)
        row = (float(rec[2]),
               parse(rec[0] + ' ' + rec[1]))
        data.insert(1, row)

    data.sort(key=lambda a: a[0])

    accounts = iter(accounts_data)
    acc_weight, acc_id = (0, 'null')

    for w,d in data:
        if acc_weight < w:
            acc_weight, acc_id = next(accounts)
            print('====== ' + acc_id + ' ======')

        print(d.isoformat() + ': ' + str(w))

if __name__ == "__main__":
    main(iter(sys.argv[1:]))
