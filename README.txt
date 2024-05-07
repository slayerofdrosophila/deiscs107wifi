Setup requierd:

Install:
hostpad mitmproxy dnsmasq iptables npm

add DNSStubListener=no to /etc/systemd/resolved.conf
then sudo systemctl restart systemd-resolved

add the output interface MAC address to /etc/NetworkManager/NetworkManager.conf
called "wifi interface" in the script
[keyfile]
unmanaged-devices=mac:e4:fa:c4:e6:d3:f8


Disable firewall
sudo ufw disable


Change the interface names to be the netwrok interfaces you want in the scripts



Script 1: SSLStrip
snoop.sh

Saves http responses by local IP / time in "saves" dir


Script 2: Phish
fish.sh

Form output is simply printed.
