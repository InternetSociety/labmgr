import {Address4, Address6} from "ip-address";
import padStart from 'lodash.padstart';

export function printable_address(address) {
    if (!address) return '?';

    // The address must be in canonical form
    let obj = new Address6(address);
    if (address.startsWith('0000:0000:0000:0000:0000:ffff:')) {
        // IPv4
        return obj.to4().correctForm();
    } else {
        // IPv6
        return obj.correctForm();
    }
}

export function printable_prefix(address, prefix_length) {
    if (!address || !prefix_length) {
        return '?';
    }

    // The address must be in canonical form
    let obj = new Address6(address);
    if (address.startsWith('0000:0000:0000:0000:0000:ffff:')) {
        // IPv4
        return obj.to4().correctForm() + '/' + (prefix_length - 96).toString();
    } else {
        // IPv6
        return obj.correctForm() + '/' + prefix_length.toString();
    }
}

export function get_v6_address(address) {
    if (address.indexOf(':') >= 0) {
        return new Address6(address);
    } else {
        return new Address6.fromAddress4(address);
    }
}

export function get_address(address) {
    if (address.indexOf(':') >= 0) {
        return new Address6(address);
    } else {
        return new Address4(address);
    }
}

export function canonical_address(address) {
    return get_v6_address(address).canonicalForm();
}

export function fix_prefix(address) {
    let obj = get_address(address);
    return obj.correctForm() + obj.subnet;
}

export function fix_address(address) {
    let obj = get_address(address);
    return obj.correctForm();
}
