#!/usr/bin/env python
"""
A little script to generate the configs for the monitors in the MANRS lab.
"""

import sys

from config import networks

my_asn = int(sys.argv[1])
my_network = networks[my_asn]

print('HOSTNAME="as{my_asn}-{my_role}"'.format(my_asn=my_asn, my_role=my_network['role']))
print('')
print('V4_INTERFACE="{link_v4}"'.format(link_v4=my_network['link_address_v4']))
print('V6_INTERFACE="{link_v6}"'.format(link_v6=my_network['link_address_v6']))
print('')
print('ROUTER_ID="{router_id}"'.format(router_id=my_network['link_address_v4'].ip))
print('LOCAL_ASN="{my_asn}"'.format(my_asn=my_asn))
print('')
print('PEER_ASN="{peer_asn}"'.format(peer_asn=my_network['peer_asn']))
peer_v4 = my_network['link_address_v4'].network[1] \
    if my_network['link_address_v4'].network[1] != my_network['link_address_v4'].ip \
    else my_network['link_address_v4'].network[0]
print('PEER_ADDRESS_V4="{peer_v4}"'.format(peer_v4=peer_v4))
peer_v6 = my_network['link_address_v6'].network[1] \
    if my_network['link_address_v6'].network[1] != my_network['link_address_v6'].ip \
    else my_network['link_address_v6'].network[0]
print('PEER_ADDRESS_V6="{peer_v6}"'.format(peer_v6=peer_v6))
print('')

for proto in ['v4', 'v6']:
    rule = 1
    for route in my_network['announced_prefixes_' + proto]:
        prefix = route[0]
        as_path = ' ' + ' '.join(map(str, route[1])) if route[1] else ''
        print('{proto}_PREFIX{nr}="{prefix}{as_path}"'.format(proto=proto.upper(), nr=rule, prefix=prefix,
                                                              as_path=as_path))
        rule += 1
    print('')

rule = 1
print('# Pings to/from valid addresses')
for proto in ['v4', 'v6']:
    if not my_network['valid_prefix_' + proto]:
        continue

    src = my_network['valid_prefix_' + proto][1]

    for other_asn, other_network in networks.items():
        if other_asn == my_asn:
            continue
        if not other_network['valid_prefix_' + proto]:
            continue

        dst = other_network['valid_prefix_' + proto][1]
        if src == dst:
            continue

        print('PING{nr}="{dst} {src}"  # to {other_asn}'.format(nr=rule, dst=dst, src=src, other_asn=other_asn))
        rule += 1

print('')
print('# Pings from bogus addresses to valid routes')
for proto in ['v4', 'v6']:
    if not my_network['bogus_address_' + proto]:
        continue

    src = my_network['bogus_address_' + proto]

    for other_asn, other_network in networks.items():
        if other_asn == my_asn:
            continue
        if not other_network['valid_prefix_' + proto]:
            continue

        dst = other_network['valid_prefix_' + proto][1]
        if src == dst:
            continue

        print('PING{nr}="{dst} {src}"  # to {other_asn}'.format(nr=rule, dst=dst, src=src, other_asn=other_asn))
        rule += 1

print('')
print('# Pings from someone else\'s addresses to valid routes')
for proto in ['v4', 'v6']:
    if not my_network['stolen_address_' + proto]:
        continue

    src = my_network['stolen_address_' + proto]

    for other_asn, other_network in networks.items():
        if other_asn == my_asn:
            continue
        if not other_network['valid_prefix_' + proto]:
            continue

        dst = other_network['valid_prefix_' + proto][1]
        if src == dst:
            continue

        print('PING{nr}="{dst} {src}"  # to {other_asn}'.format(nr=rule, dst=dst, src=src, other_asn=other_asn))
        rule += 1

print('')
print('# Pings from valid address to bogus address')
for proto in ['v4', 'v6']:
    if not my_network['valid_prefix_' + proto]:
        continue

    src = my_network['valid_prefix_' + proto][1]

    for other_asn, other_network in networks.items():
        if other_asn == my_asn:
            continue
        if ('bogus_address_' + proto) not in other_network:
            continue

        dst = other_network['bogus_address_' + proto]
        if src == dst:
            continue

        print('PING{nr}="{dst} {src}"  # to {other_asn}'.format(nr=rule, dst=dst, src=src, other_asn=other_asn))
        rule += 1

print('')
print('# Pings from bogus address to bogus address')
for proto in ['v4', 'v6']:
    if not my_network['bogus_address_' + proto]:
        continue

    src = my_network['bogus_address_' + proto]

    for other_asn, other_network in networks.items():
        if other_asn == my_asn:
            continue
        if ('bogus_address_' + proto) not in other_network:
            continue

        dst = other_network['bogus_address_' + proto]
        if src == dst:
            continue

        print('PING{nr}="{dst} {src}"  # to {other_asn}'.format(nr=rule, dst=dst, src=src, other_asn=other_asn))
        rule += 1

print('')
print('# Pings from some else\'s address to bogus address')
for proto in ['v4', 'v6']:
    if not my_network['stolen_address_' + proto]:
        continue

    src = my_network['stolen_address_' + proto]

    for other_asn, other_network in networks.items():
        if other_asn == my_asn:
            continue
        if ('bogus_address_' + proto) not in other_network:
            continue

        dst = other_network['bogus_address_' + proto]
        if src == dst:
            continue

        print('PING{nr}="{dst} {src}"  # to {other_asn}'.format(nr=rule, dst=dst, src=src, other_asn=other_asn))
        rule += 1
