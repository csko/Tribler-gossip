#!/usr/bin/env python2

import os
import math
from collections import defaultdict

D = "experiment/logs/"

def get_stats(res):
    """Returns num, max, avg, sum, var, med"""

    numr = len(res)
    if numr == 0:
        return (0, 0, 0, 0, 0, 0)

    maxr = -10000
    minr = +10000
    sumr = 0
    varr = 0

    for i in res:
        if i > maxr:
            maxr = i
        if i < minr:
            minr = i
        sumr += i
#        print i

    # variance
    avgr = float(sumr) / numr

    s = 0.0
    for i in res:
        d = i - avgr
        d *= d
        s += d

    s /= numr
    varr = math.sqrt(s)

    res.sort()

    if numr % 2 == 1:
        med = res[numr/2]
    else:
        med = (res[numr/2-1] + res[numr/2]) / 2.0

    return {'num' : numr, 'min' : minr, 'max' : maxr, 'avg' : avgr,
            'sum' : sumr, 'var' : varr, 'med' : med}

def load_data():
    data = []
    for d in os.listdir(D):
        with open(D + d) as f:
            f.readline()
            for line in f:
                row = line[:-1].split()
                data.append((int(row[0]), int(row[1]), float(row[3])))
    return data

# TODO: do a faster, but not so accurate version using a fix set of intervals

def print_stats(t, s):
    stats = get_stats(s.values())
    vals = [stats['min'], stats['max'], stats['avg']]
    print t, " ".join([str(x) for x in vals])

def accurate_stats():
    peer_data = defaultdict(float) # maps a peer ID to their last known prediction value

    print "# timestamp min max avg"

    first_t = None
    for d in sorted(data):
        t = d[0]

        if first_t == None:
            t = 0
            first_t = d[0]
        else:
            t = d[0] - first_t

        peer_data[d[1]] = d[2]
        print_stats(t, peer_data)

data = load_data()
accurate_stats()

