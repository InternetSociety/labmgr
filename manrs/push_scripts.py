#!/usr/bin/env python3
import glob
import json
import os
import sys

import pexpect

import config

with open(sys.argv[1], 'r') as file:
    project = json.load(file)

for node in project['topology']['nodes']:
    if node['name'].startswith('AS'):
        asn = int(node['name'][2:])
        if asn in config.networks:
            network = config.networks[asn]
            if network['role'] == 'student':
                continue

            print("Connecting to {}".format(node['name']))
            console = pexpect.spawn('telnet', ['::1', str(node['console'])], timeout=5)

            # Clean input buffer
            try:
                while True:
                    console.expect([
                        r'@.*:.*\$ ',
                        r'@.*:.*# ',
                    ], timeout=2)
            except pexpect.exceptions.TIMEOUT:
                pass

            console.sendline('')

            done = False
            while not done:
                index = console.expect([
                    r'[Ll]ogin:',
                    r'[Pp]assword:',
                    r'@.*:.*\$ ',
                    r'@.*:.*# ',
                ])

                if index == 0:
                    print('- Sending username')
                    console.sendline('gns3')
                elif index == 1:
                    print('- Sending password')
                    console.sendline('gns3')
                elif index == 2:
                    print('- Become root')
                    console.sendline('sudo -s')
                elif index == 3:
                    done = True

            # Replace /etc/issue
            print('- Update /etc/issue')
            console.sendline('cat > /etc/issue')
            console.sendline("ISOC Monitor {} (based on Bird 1.5.0 on Core Linux)".format(config.version))
            console.sendline('')
            console.sendline("username 'gns3', password 'gns3'")
            console.sendline("Run filetool.sh -b if you want to save your changes")
            console.sendeof()
            console.expect(r'@.*:(?P<path>.*)# ')

            # Remove legacy files
            print('- Remove legacy /opt/configure_routes.sh')
            console.sendline('rm -f /opt/configure_routes.sh')
            console.expect(r'@.*:(?P<path>.*)# ')

            # Find all files to upload
            filenames = glob.glob('opt/**', recursive=True)
            for filename in filenames:
                if os.path.isdir(filename):
                    # Make directory
                    print('- Make directory /{}'.format(filename))
                    console.sendline('mkdir -p /{}'.format(filename))
                    console.expect(r'@.*:(?P<path>.*)# ')
                else:
                    # Upload file
                    print('- Upload file /{}'.format(filename))
                    console.sendline('cat > /{}'.format(filename))
                    for line in open(filename).readlines():
                        line = line.rstrip('\r\n')
                        console.sendline(line)
                    console.sendeof()
                    console.expect(r'@.*:(?P<path>.*)# ')

                    if filename.endswith('.sh'):
                        print('  - Making file executable')
                        console.sendline('chmod +x /{}'.format(filename))
                        console.expect(r'@.*:(?P<path>.*)# ')

            print('- Write customised /opt/settings.sh')
            console.sendline('cat > /opt/settings.sh')

            settings = pexpect.run('python3 generate_settings.py {}'.format(asn)).splitlines()
            for setting in settings:
                console.sendline(setting)
            console.sendeof()
            console.expect(r'@.*:(?P<path>.*)# ')

            print("- Saving configuration")
            console.sendline('filetool.sh -b')
            console.expect(r'@.*:(?P<path>.*)# ')

            print("- Rebooting")
            console.sendline('reboot')

            print("")
