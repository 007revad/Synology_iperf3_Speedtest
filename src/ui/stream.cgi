#!/bin/bash

echo "Content-Type: text/event-stream"
echo "Cache-Control: no-cache"
echo ""

#for i in $(seq 1 10); do
#    echo "data: tick $i at $(date +%s.%N)"
#    echo ""
#    sleep 1
#done

# stdbuf -oL forces line-buffered output from ping instead of fully-buffered,
# which is the same class of problem iperf3's own output could hit
#stdbuf -oL ping -i 1 8.8.8.8 | while IFS= read -r line; do
#    echo "data: $line"
#    echo ""
#done

# results in "data: ping: socket: Operation not permitted"
#stdbuf -oL ping -i 1 8.8.8.8 2>&1 | while IFS= read -r line; do
#    echo "data: $line"
#    echo ""
#done

iperf3 -c 192.168.20.200 -t 10 --forceflush
