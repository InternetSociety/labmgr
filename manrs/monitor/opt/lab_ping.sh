#!/bin/sh

DST=$1
SRC=$2

if [[ -z "${DST}" ]]; then
	echo "Usage: $0 <dst> [src]"
	exit 1
fi

OPT="-q"
if [[ -n "${SRC}" ]]; then
	OPT="${OPT} -I ${SRC}"
fi

(while true; do
	ping ${OPT} ${DST}
	sleep 1
done)
