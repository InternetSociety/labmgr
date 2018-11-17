#!/bin/sh

cd /opt
source settings.sh

VERSION="$1"
if [[ "$VERSION" == "4" ]]; then
	MY_ADDRESS=$(echo ${V4_INTERFACE} | cut -d/ -f1)
	PEER_ADDRESS="${PEER_ADDRESS_V4}"
elif [[ "$VERSION" == "6" ]]; then
	MY_ADDRESS=$(echo ${V6_INTERFACE} | cut -d/ -f1)
	PEER_ADDRESS="${PEER_ADDRESS_V6}"
else
	echo "Please specify 4 or 6" >&2
	exit 1
fi

STATIC_ROUTES=""
EXPORT_FILTERS=""

i=1
while true; do
	eval CURRENT_PREFIX="\${V${VERSION}_PREFIX${i}}"
	if [[ -z "${CURRENT_PREFIX}" ]]; then
		break
	fi

	set -- ${CURRENT_PREFIX}

	STATIC_ROUTES="${STATIC_ROUTES}\troute $1 unreachable;\n"

	if [[ -n "$2" ]]; then
		EXPORT_FILTERS="${EXPORT_FILTERS}\t\t\tif net = $1 then {\n"
		shift
		while [[ -n "$1" ]]; do
			EXPORT_FILTERS="${EXPORT_FILTERS}\t\t\t\tbgp_path.prepend($1);\n"
			shift
		done
		EXPORT_FILTERS="${EXPORT_FILTERS}\t\t\t}\n"
	fi

	let i=$i+1
done

cat /opt/bird.conf.tpl \
	| sed -e "s@\${ROUTER_ID}@${ROUTER_ID}@g" \
	| sed -e "s@\${STATIC_ROUTES}@${STATIC_ROUTES}@g" \
	| sed -e "s@\${LOCAL_ASN}@${LOCAL_ASN}@g" \
	| sed -e "s@\${MY_ADDRESS}@${MY_ADDRESS}@g" \
	| sed -e "s@\${PEER_ADDRESS}@${PEER_ADDRESS}@g" \
	| sed -e "s@\${PEER_ASN}@${PEER_ASN}@g" \
	| sed -e "s@\${EXPORT_FILTERS}@${EXPORT_FILTERS}@g"
