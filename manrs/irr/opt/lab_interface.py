#!/usr/bin/env python3
import fcntl
import os
import re
import select
import subprocess
import sys
import time

header = re.compile(r'^\*\*\*\*\*\[ +(.*?) +\]\*\*\*\*\*$')
separator = re.compile(r'^-+$')


def print_header(title):
    print('*****[ {} ]*****'.format(title))


def send_uuid():
    print_header("UUID")

    uuid = open('/sys/devices/virtual/dmi/id/product_uuid', 'r').read().strip()
    print(uuid)


def send_report():
    print_header('NEIGHBORS')
    result = subprocess.run(['whois', '-h', 'localhost', '--', 'AS64500'],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, timeout=5, universal_newlines=True)
    for line in result.stdout.split('\n'):
        line = line.rstrip()

        if line.startswith('import:') or line.startswith('export:') or \
                line.startswith('mp-import:') or line.startswith('mp-export:'):
            print(line)

    print_header('ASN IPv4')
    subprocess.run(['bgpq3', '-4', '-j', '-p', '-h', 'localhost', '-S', 'MANRS', '-l', 'filter', 'AS64500'],
                   stdin=subprocess.DEVNULL, timeout=5, universal_newlines=True)

    print_header('ASN IPv6')
    subprocess.run(['bgpq3', '-6', '-j', '-p', '-h', 'localhost', '-S', 'MANRS', '-l', 'filter', 'AS64500'],
                   stdin=subprocess.DEVNULL, timeout=5, universal_newlines=True)

    print_header('AS-SET IPv4')
    subprocess.run(['bgpq3', '-4', '-j', '-p', '-h', 'localhost', '-S', 'MANRS', '-l', 'filter', 'AS64500:AS-ALL'],
                   stdin=subprocess.DEVNULL, timeout=5, universal_newlines=True)

    print_header('AS-SET IPv6')
    subprocess.run(['bgpq3', '-6', '-j', '-p', '-h', 'localhost', '-S', 'MANRS', '-l', 'filter', 'AS64500:AS-ALL'],
                   stdin=subprocess.DEVNULL, timeout=5, universal_newlines=True)


readline_buffer = ''


def timed_readline(timeout=60):
    """
    Very inefficient readline with timeout

    :return: String, or None on timeout
    """
    global readline_buffer

    # Immediately return if there is enough in the buffer
    parts = readline_buffer.split('\n', 1)
    if len(parts) == 2:
        readline_buffer = parts[1]
        return parts[0] + '\n'

    while True:
        # Otherwise read more first
        ready = select.select([sys.stdin], [], [], timeout)[0]
        if not ready:
            return None

        readline_buffer += sys.stdin.read()
        parts = readline_buffer.split('\n', 1)
        if len(parts) == 2:
            readline_buffer = parts[1]
            return parts[0] + '\n'


def run():
    current = ''
    buffer = ''

    # Send report on startup
    send_uuid()
    send_report()
    print_header('END')

    while True:
        try:
            line = timed_readline()
            if line is None:
                # Timed out, send report
                send_uuid()
                send_report()
                print_header('END')
                continue

            match = header.match(line.rstrip())
            if match:
                name = match.group(1)

                if name in ['UPDATE', 'QUERY', 'ID']:
                    current = name
                    buffer = ''
                elif name == 'END':
                    send_uuid()

                    if current != 'ID':
                        print_header(current + '-RESULT')

                        # Process
                        if current == 'QUERY':
                            subprocess.run(['whois', '-h', 'localhost', '--', buffer],
                                           stdin=subprocess.DEVNULL, timeout=5, universal_newlines=True)

                        elif current == 'UPDATE':
                            result = subprocess.run(
                                ['irr_rpsl_submit', '-N', '-D', '-x'],
                                input=buffer, stdout=subprocess.PIPE, timeout=10, universal_newlines=True)

                            started = False
                            skip_newlines = True
                            seen_newline = False
                            for line in result.stdout.split('\n'):
                                line = line.rstrip()

                                if separator.match(line):
                                    started = not started
                                    skip_newlines = True

                                elif line == '':
                                    if not skip_newlines:
                                        seen_newline = True

                                elif 'mail headers' in line or line.startswith('- '):
                                    continue

                                elif started:
                                    if seen_newline:
                                        print('')
                                    skip_newlines = False
                                    seen_newline = False
                                    print(line)

                            send_report()

                    print_header('END')

                    current = ''
                    buffer = ''
                else:
                    # Bad input: ignore
                    current = ''
                    buffer = ''
            else:
                # Add to buffer
                buffer += line

        except IOError as e:
            print("Exception: {}".format(e), file=sys.stderr)
            time.sleep(5)

        except Exception as e:
            print("Exception: {}".format(e), file=sys.stderr)


if __name__ == '__main__':
    # set sys.stdin non-blocking
    orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
    fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

    try:
        run()
    finally:
        # set sys.stdin non-blocking
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl & ~os.O_NONBLOCK)
