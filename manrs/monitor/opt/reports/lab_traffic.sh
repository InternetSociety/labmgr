#!/bin/sh
/opt/tools/lab_section.sh "Received traffic"
dmesg -c | fgrep PROTO=ICMP | fgrep -v "=fe80:" | cut -d ' ' -f 4,5 | sort -u
