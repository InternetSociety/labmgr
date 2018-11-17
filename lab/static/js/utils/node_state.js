import {canonical_address, canonical_prefix, fix_address, get_address, get_v6_address} from "./addresses";

const traffic_line = /^SRC=([0-9a-f.:]+) +DST=([0-9a-f.:]+)$/i;
const route_line = /^([0-9a-f.:]+\/[0-9]+) +(via +([0-9a-f.:]+) +on +([0-9a-z.:]+) \[([0-9a-z]+) .*])?/i;
const route_attr_line = /^\s+([0-9a-z._]+): +(.+)$/i;
const irr_neighbors_import_line = /^mp-import:\s+from\s+(AS[0-9]+)\s+accept\s+(.*?)\s*$/i;
const irr_neighbors_export_line = /^mp-export:\s+to\s+(AS[0-9]+)\s+announce\s+(.*?)\s*$/i;

export function compare(a, b) {
    let result;
    if (a instanceof Array && b instanceof Array) {
        // Compare lengths, then item by item
        if (a.length < b.length) {
            return -1;
        } else if (a.length > b.length) {
            return 1;
        }

        for (let [idx, item] of a.entries()) {
            if ((result = compare(item, b[idx])) !== 0) {
                return result;
            }
        }
        return 0;
    } else if (a instanceof Object && b instanceof Object) {
        if (a.prefix || b.prefix) {
            if ((result = compare_prefixes(a, b)) !== 0) {
                return result;
            }
        } else {
            for (let key of Object.keys(a).sort()) {
                if ((result = compare(a[key], b[key])) !== 0) {
                    return result;
                }
            }
            for (let key of Object.keys(b).sort()) {
                if ((result = compare(a[key], b[key])) !== 0) {
                    return result;
                }
            }
        }
        return 0;
    } else {
        if (a < b || ((a === null || a === undefined) && (b !== null && b !== undefined))) {
            return -1;
        } else if (a > b || ((a !== null && a !== undefined) && (b === null || b === undefined))) {
            return 1;
        } else {
            return 0;
        }
    }
}

export function compare_prefixes(a, b) {
    if (!a.prefix) {
        return 1;
    } else if (!b.prefix) {
        return -1;
    }
    if (a.prefix < b.prefix) {
        return -1;
    } else if (a.prefix > b.prefix) {
        return 1;
    } else if (a.prefix_length < b.prefix_length) {
        return -1;
    } else if (a.prefix_length > b.prefix_length) {
        return 1;
    } else {
        return 0;
    }
}

export function compare_states(states) {
    for (const state of Object.values(states)) {
        if (compare(state.goal, state.state) !== 0) {
            return false;
        }
    }
    return true;
}

function convert_traffic_state(state) {
    const lines = state.split(/\r\n|\r|\n/).filter(l => l.trim() !== '');

    // Use strings in a set to eliminate duplicates
    let traffic = new Set();
    for (let line of lines) {
        let match = line.match(traffic_line);
        if (!match) continue;

        traffic.add(canonical_address(match[1]) + '-' + canonical_address(match[2]));
    }

    let output = [...traffic].map(l => l.split('-'));
    return output.sort();
}

function convert_route_state(state) {
    const lines = state.split(/\r\n|\r|\n/).filter(l => l.trim() !== '');

    let line = lines.shift();
    if (line !== 'BIRD 1.5.0 ready.') {
        return [];
    }

    let routes = [];
    let currentRoute = null;
    while ((line = lines.shift()) !== undefined) {
        // Look for a new route
        let match = line.match(route_line);
        if (match) {
            // Do we need to store the previous route?
            if (currentRoute) routes.push(currentRoute);

            // Start of a new route
            currentRoute = {
                prefix: get_v6_address(match[1]).canonicalForm(),
                prefix_length: get_address(match[1]).subnetMask,
                next_hop: fix_address(match[3]),
                next_hop_intf: match[4],
                proto: match[5],
            };
        } else if (currentRoute) {
            // Maybe data for the current route?
            match = line.match(route_attr_line);
            if (match) {
                // Route attribute found
                let key = match[1].toLowerCase();
                let value = match[2];

                switch (key) {
                    case 'type':
                        value = value.split(' ');
                        break;
                    case 'bgp.as_path':
                        value = value.split(' ').map(asn => parseInt(asn, 10));
                        break;
                    case 'bgp.next_hop':
                        value = fix_address(value);
                        break;
                    case 'bgp.local_pref':
                        value = parseInt(value, 10);
                        break;
                }
                currentRoute[key] = value;
            }
        }
    }

    // Do we need to store the previous route?
    if (currentRoute) routes.push(currentRoute);

    routes.sort(compare_prefixes);

    return routes;
}

function convert_irr_prefixes_state(state) {
    let data;
    try {
        data = JSON.parse(state);
    } catch (e) {
        return [];
    }
    let prefixes = [];
    for (let entry of data.filter) {
        let prefix = get_v6_address(entry.prefix);
        prefixes.push({
            prefix: prefix.canonicalForm(),
            prefix_length: prefix.subnetMask,
        })
    }
    prefixes.sort();
    return prefixes;
}

function convert_irr_neighbors(state) {
    const lines = state.split(/\r\n|\r|\n/).filter(l => l.trim() !== '');
    let neighbors = {};

    for (let line of lines) {
        let match, direction;
        if (match = line.match(irr_neighbors_import_line)) {
            direction = 'import';
        }
        else if (match = line.match(irr_neighbors_export_line)) {
            direction = 'export';
        } else {
            continue;
        }

        if (!neighbors[match[1]]) {
            neighbors[match[1]] = {
                import: [],
                export: [],
            }
        }
        neighbors[match[1]][direction].push(match[2]);
    }

    console.log(neighbors);
    return neighbors;
}

export function convert_state(goal_type, state) {
    switch (goal_type) {
        case 'Received traffic':
            return convert_traffic_state(state);

        case 'Routes IPv4':
        case 'Routes IPv6':
            return convert_route_state(state);

        case 'ASN IPv4':
        case 'ASN IPv6':
        case 'AS-SET IPv4':
        case 'AS-SET IPv6':
            return convert_irr_prefixes_state(state);

        case 'NEIGHBORS':
            return convert_irr_neighbors(state);

        default:
            return state;
    }
}

export function convert_goal(goal_type, goal) {
    return {
        ...goal,
        goal: convert_state(goal_type, goal.goal),
        state: convert_state(goal_type, goal.state),
    };
}

export function convert_goals(states) {
    let output = {};
    for (const [goal_type, state] of Object.entries(states)) {
        output[goal_type] = convert_goal(goal_type, state);
    }
    return output;
}

export function convert_node(node) {
    if (!node.state)
        return node;

    return {
        ...node,
        state: convert_goals(node.state),
    };
}

export function convert_nodes(nodes) {
    let output = {};
    for (const [node_id, node] of Object.entries(nodes)) {
        output[node_id] = convert_node(node);
    }
    return output;
}
