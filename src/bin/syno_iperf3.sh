#!/bin/bash
# syno_iperf3.sh - core iperf3 invocation, callable standalone or
# wrapped by stream.cgi / api.cgi. Emits plain iperf3 output on
# stdout - no SSE framing here, that's the caller's job.
#
# Usage:
#   syno_iperf3.sh client <target> <port> <protocol> <mode> <streams> [bandwidth]
#   syno_iperf3.sh server-oneoff [port]

iperf3=/var/packages/Synoiperf3/target/bin/iperf3/iperf3

action="$1"; shift

case "$action" in
client)
    target="$1"; port="${2:-5201}"; protocol="${3:-tcp}"
    mode="${4:-upload}"; streams="${5:-1}"; bandwidth="${6:-0}"

    if [[ ! "$target" =~ ^[a-zA-Z0-9.-]+$ ]]; then
        echo "error: invalid target" >&2; exit 1
    fi
    if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
        echo "error: invalid port" >&2; exit 1
    fi
    if [[ ! "$streams" =~ ^[0-9]+$ ]] || (( streams < 1 || streams > 128 )); then
        echo "error: invalid streams" >&2; exit 1
    fi

    cmd=("$iperf3" -c "$target" -p "$port" -P "$streams" -t 10 --forceflush)
    [[ "$protocol" == "udp" ]] && cmd+=(-u -b "$bandwidth")
    [[ "$mode" == "download" ]] && cmd+=(-R)

    stdbuf -oL "${cmd[@]}" 2>&1
    ;;

server-oneoff)
    port="${1:-5201}"
    if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
        echo "error: invalid port" >&2; exit 1
    fi
    stdbuf -oL "$iperf3" -s -1 -p "$port" --forceflush
    ;;

*)
    echo "error: unknown action '$action'" >&2
    exit 1
    ;;
esac
