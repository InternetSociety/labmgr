/*
 * MANRS Lab
 */

# Override router ID
router id ${ROUTER_ID};

# Don't display timestamps in route tables
timeformat route "HIDDEN";

# This pseudo-protocol performs synchronization between BIRD's routing
# tables and the kernel.
protocol kernel {
	persist;		# Don't remove routes on bird shutdown
	scan time 20;		# Scan kernel routing table every 20 seconds
	export all;		# Default is export none
}

# This pseudo-protocol watches all interface up/down events.
protocol device {
	scan time 10;		# Scan interfaces every 10 seconds
}

# Static routes (again, there can be multiple instances, so that you
# can disable/enable various groups of static routes on the fly).
protocol static {
${STATIC_ROUTES}
}

protocol bgp {
	local ${MY_ADDRESS} as ${LOCAL_ASN};
	neighbor ${PEER_ADDRESS} as ${PEER_ASN};
	export filter {
		if source = RTS_STATIC then {
			bgp_path.empty;

${EXPORT_FILTERS}

			bgp_path.prepend(${LOCAL_ASN});
			accept;
		}
		reject;
	};
}
