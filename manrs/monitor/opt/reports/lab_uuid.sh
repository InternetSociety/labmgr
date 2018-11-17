#!/bin/sh
/opt/tools/lab_section.sh "UUID"
PART1=$(cat /sys/devices/virtual/dmi/id/product_uuid | cut -d '-' -f 1 | sed -e 'G;:1' -e 's/\(..\)\(.*\n\)/\2\1/;t1' -e 's/.//')
PART2=$(cat /sys/devices/virtual/dmi/id/product_uuid | cut -d '-' -f 2 | sed -e 'G;:1' -e 's/\(..\)\(.*\n\)/\2\1/;t1' -e 's/.//')
PART3=$(cat /sys/devices/virtual/dmi/id/product_uuid | cut -d '-' -f 3 | sed -e 'G;:1' -e 's/\(..\)\(.*\n\)/\2\1/;t1' -e 's/.//')
PART4=$(cat /sys/devices/virtual/dmi/id/product_uuid | cut -d '-' -f 4)
PART5=$(cat /sys/devices/virtual/dmi/id/product_uuid | cut -d '-' -f 5)

echo ${PART1}-${PART2}-${PART3}-${PART4}-${PART5}
