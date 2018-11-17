#!/bin/sh
# put other system startup commands here
modprobe ipv6
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1

# This waits until all devices have registered
/sbin/udevadm settle --timeout=10

# Load settings
cd /opt
source settings.sh

# Set hostname
/usr/bin/sethostname ${HOSTNAME}

# configure static interface addresses and routes
ip link set dev eth0 up
ip -4 addr add dev eth0 ${V4_INTERFACE}
ip -6 addr add dev eth0 ${V6_INTERFACE}

ip link set dev dummy0 up
i=1
while true; do
	eval CURRENT_PING="\${PING${i}}"
	if [[ -z "${CURRENT_PING}" ]]; then
		break
	fi

	set -- ${CURRENT_PING}

	ip addr add dev dummy0 $2

	let i=$i+1
done

# Log all ICMP packets for analysis
iptables -A INPUT -i eth0 -p icmp --icmp-type 8 -j LOG
iptables -A FORWARD -i eth0 -p icmp --icmp-type 8 -j LOG
ip6tables -A INPUT -i eth0 -p icmpv6 --icmpv6-type 128 -j LOG
ip6tables -A FORWARD -i eth0 -p icmpv6 --icmpv6-type 128 -j LOG

# Generate bird config
/opt/generate_config.sh 4 > /usr/local/etc/bird/bird.conf
/opt/generate_config.sh 6 > /usr/local/etc/bird/bird6.conf

# Start routing
/usr/local/sbin/bird -u gns3 -g staff
/usr/local/sbin/bird6 -u gns3 -g staff

sleep 2

# Start background pings
i=1
while true; do
	eval CURRENT_PING="\${PING${i}}"
	if [[ -z "${CURRENT_PING}" ]]; then
		break
	fi

	set -- ${CURRENT_PING}

	/opt/lab_ping.sh $1 $2 &

	let i=$i+1
done

# Start monitoring
/opt/lab_report.sh > /dev/ttyS1 &
