#!/bin/bash

# 1: Set up AP
# 2: Set up node server
# 3: Set up ... smaller server

# Function to clean up on exit
cleanup() {
    echo "Stopping processes..."
    pkill dnsmasq
    kill $(jobs -p)
}

# Trap signals like SIGINT (Ctrl + C)
trap cleanup EXIT

# Start the processes in the background
./mitm_ap.sh &
mitmdump --quiet --showhost -s sslstrip.py &

# Wait for all background processes to finish
wait
