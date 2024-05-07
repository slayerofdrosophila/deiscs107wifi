#!/bin/bash

# Configuration variables
WIFI_INTERFACE="wlo1"       # Your wireless interface name
INTERNET_INTERFACE="wlx3c3332cf3088"      # Your internet-facing interface name
SSID="bingchilling"                    # SSID of your Wi-Fi network
PASSWORD="12345678"            # Wi-Fi password
CHANNEL=6                      # Wi-Fi channel
GATEWAY_IP="192.168.10.1"      # IP for the Wi-Fi interface on your hotspot
SUBNET="192.168.10.0/24"       # Subnet for the DHCP service
DNS_SERVER="8.8.8.8"           # DNS server to use for your Wi-Fi network


# Dependencies check
if ! command -v hostapd >/dev/null || ! command -v dnsmasq >/dev/null || ! command -v iptables >/dev/null; then
    echo "Error: Make sure hostapd, dnsmasq, and iptables are installed." >&2
    exit 1
fi


# Generate hostapd.conf
cat > hostapd.conf <<EOF
interface=$WIFI_INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Start hostapd
hostapd hostapd.conf &
HOSTAPD_PID=$!

# Configure system for IP forwarding and NAT
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -o $INTERNET_INTERFACE -j MASQUERADE
iptables -A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $WIFI_INTERFACE -o $INTERNET_INTERFACE -j ACCEPT

# Disable redirects
sysctl -w net.ipv4.conf.all.send_redirects=0


# Forward to mitmproxy... which will take care of the rest
# Forwards HTTPS traffic too... Do we need it?
iptables -t nat -A PREROUTING -i $WIFI_INTERFACE -p tcp --dport 80 -j REDIRECT --to-port 8080

# Dont proxy HTTPS traffic, beacuse we dont have the cert installed
# Nevermind
iptables -t nat -A PREROUTING -i $WIFI_INTERFACE -p tcp --dport 443 -j REDIRECT --to-port 8080

ip6tables -t nat -A PREROUTING -i $WIFI_INTERFACE -p tcp --dport 80 -j REDIRECT --to-port 8080
ip6tables -t nat -A PREROUTING -i $WIFI_INTERFACE -p tcp --dport 443 -j REDIRECT --to-port 8080


# Assign static IP to the Wi-Fi interface
ip addr add $GATEWAY_IP/24 dev $WIFI_INTERFACE

# Start dnsmasq for DHCP and DNS
# dnsmasq --interface=$WIFI_INTERFACE --dhcp-range=${GATEWAY_IP%.*}.10,${GATEWAY_IP%.*}.250,255.255.255.0,12h --address=/example.com/192.168.4.211 --address=/bing.com/192.168.4.211 &

# Find local IP addr
LOCAL_IP=$(/home/cool/sec/local_ip.py)
LOCAL_IP=192.168.5.111
echo ${LOCAL_IP}

dnsmasq --interface=$WIFI_INTERFACE --dhcp-range=${GATEWAY_IP%.*}.10,${GATEWAY_IP%.*}.250,255.255.255.0,12h --log-queries --log-facility=/var/log/dns.log &

tail -f /var/log/dns.log | grep 'query\[' > /home/cool/sec/queries.log &


# Cleanup function
cleanup() {
    echo "Cleaning up..."
    kill $HOSTAPD_PID
    ip addr del $GATEWAY_IP/24 dev $WIFI_INTERFACE
    iptables -t nat -D POSTROUTING -o $INTERNET_INTERFACE -j MASQUERADE
    iptables -D FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
    iptables -D FORWARD -i $WIFI_INTERFACE -o $INTERNET_INTERFACE -j ACCEPT

    iptables -t nat -D PREROUTING -i $WIFI_INTERFACE -p tcp --dport 80 -j REDIRECT --to-port 8080
    iptables -t nat -D PREROUTING -i $WIFI_INTERFACE -p tcp --dport 443 -j REDIRECT --to-port 8080

    ip6tables -t nat -D PREROUTING -i $WIFI_INTERFACE -p tcp --dport 80 -j REDIRECT --to-port 8080
    ip6tables -t nat -D PREROUTING -i $WIFI_INTERFACE -p tcp --dport 443 -j REDIRECT --to-port 8080
    sysctl -w net.ipv4.ip_forward=0
    sysctl -w net.ipv4.conf.all.send_redirects=1
    pkill dnsmasq
    echo "Done"
}

# Wait for SIGINT (Ctrl+C) and then cleanup
trap cleanup SIGINT
wait $HOSTAPD_PID

