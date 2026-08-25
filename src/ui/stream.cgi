#!/bin/bash
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

SCRIPT_DIR="$(dirname "$0")"

"${SCRIPT_DIR}/../bin/syno_iperf3.sh" client \
    "${PARAM[target]}" "${PARAM[port]:-5201}" "${PARAM[protocol]:-tcp}" \
    "${PARAM[mode]:-upload}" "${PARAM[streams]:-1}" "${PARAM[bandwidth]:-0}" \
    2>&1 | while IFS= read -r line; do
        echo "data: $line"
        echo ""
    done
