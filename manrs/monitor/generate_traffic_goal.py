#!/usr/bin/env python
"""
A little script to generate the goal conditions for the MANRS lab.
"""

from config import networks

for my_asn, my_network in networks.items():
    if my_network['role'] == 'student':
        continue

    print("# Lab goal of AS{}".format(my_asn))
    for proto in ['v4', 'v6']:
        if not my_network['valid_prefix_' + proto]:
            continue

        dst = my_network['valid_prefix_' + proto][1]

        for other_asn, other_network in networks.items():
            if other_asn == my_asn or other_network['role'] == 'student':
                continue
            if my_network['role'] in ['transit', 'peer'] and other_network['role'] != 'customer':
                continue
            if not other_network['valid_prefix_' + proto]:
                continue

            src = other_network['valid_prefix_' + proto][1]
            print('SRC={src} DST={dst}'.format(dst=dst.exploded, src=src.exploded))

    rule = 1

    print('')
