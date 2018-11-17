#!/bin/sh

rm -f /tmp/lab_report.prev
touch /tmp/lab_report.prev

count=0

while true; do
	/opt/reports/lab_uuid.sh > /tmp/lab_report.new
	/opt/reports/lab_routes_ipv4.sh >> /tmp/lab_report.new
	/opt/reports/lab_routes_ipv6.sh >> /tmp/lab_report.new
	/opt/reports/lab_traffic.sh >> /tmp/lab_report.new
	/opt/tools/lab_section.sh "END" >> /tmp/lab_report.new

	if ! diff /tmp/lab_report.prev /tmp/lab_report.new > /dev/null; then
		cat /tmp/lab_report.new
		mv /tmp/lab_report.new /tmp/lab_report.prev
		count=0
	else
		let count=$count+1
		if [[ ${count} -ge 11 ]]; then
			rm -f /tmp/lab_report.prev
			touch /tmp/lab_report.prev
		fi
	fi

	sleep 5
done
