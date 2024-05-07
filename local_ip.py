#!/usr/bin/python3

import re
import subprocess

def get_hotspot_ip(interface_name):
    # Run the 'ip addr' command and capture its output
    result = subprocess.run(['ip', 'addr'], stdout=subprocess.PIPE)
    ip_addr_output = result.stdout.decode('utf-8')

    # Regex to find the IP address of the specified interface
    ip_regex = rf"{interface_name}:.*?inet (\d+\.\d+\.\d+\.\d+)/\d+"
    match = re.search(ip_regex, ip_addr_output, re.DOTALL)

    if match:
        return match.group(1)  # Return the first matching IP address
    else:
        return "IP address not found."

interface_name = "wlx3c3332cf3088"  # Change this to your interface's name
ip_address = get_hotspot_ip(interface_name)

print(ip_address)
