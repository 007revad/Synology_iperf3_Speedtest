#!/bin/bash
# Syno_iperf3_Speedtest - runs iperf3 client test, streams live output as SSE

echo "Content-Type: text/event-stream"
echo "Cache-Control: no-cache"
echo ""

urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }
declare -A PARAM
IFS='&' read -ra kv_pairs <<< "$QUERY_STRING"
for pair in "${kv_pairs[@]}"; do
    IFS='=' read -r key val <<< "$pair"
    PARAM["$(urldecode "$key")"]="$(urldecode "$val")"
done

target="${PARAM[target]}"
port="${PARAM[port]:-5201}"
protocol="${PARAM[protocol]:-tcp}"
mode="${PARAM[mode]:-upload}"
streams="${PARAM[streams]:-1}"
bandwidth="${PARAM[bandwidth]:-0}"

if [[ ! "$target" =~ ^[a-zA-Z0-9.-]+$ ]]; then
    echo "data: error: invalid target"; echo ""; exit 1
fi
if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
    echo "data: error: invalid port"; echo ""; exit 1
fi
if [[ ! "$streams" =~ ^[0-9]+$ ]] || (( streams < 1 || streams > 128 )); then
    echo "data: error: invalid streams"; echo ""; exit 1
fi

cmd=(iperf3 -c "$target" -p "$port" -P "$streams" -t 10 --forceflush)
[[ "$protocol" == "udp" ]] && cmd+=(-u -b "$bandwidth")
[[ "$mode" == "download" ]] && cmd+=(-R)

stdbuf -oL "${cmd[@]}" 2>&1 | while IFS= read -r line; do
    echo "data: $line"
    echo ""
done
