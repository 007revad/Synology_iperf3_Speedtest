#!/bin/bash
#----------------------------------------------------------
# Syno_iperf3_Speedtest package - API CGI
# No privilege escalation - iperf3 needs no elevated access.
#----------------------------------------------------------

PKG_NAME="Synoiperf3"
PKG_ROOT="/var/packages/${PKG_NAME}"
TARGET_DIR="${PKG_ROOT}/target"
BIN_DIR="${TARGET_DIR}/bin"

dsm=$(/usr/syno/bin/synogetkeyvalue /etc.defaults/VERSION majorversion)
if [[ $dsm -ge 7 ]]; then
    VAR_DIR="${PKG_ROOT}/var"
else
    VAR_DIR="${PKG_ROOT}/etc"
fi

LOG_FILE="${VAR_DIR}/api.log"
CONF_FILE="${VAR_DIR}/syno_iperf3.conf"
touch "${LOG_FILE}"; chmod 644 "${LOG_FILE}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"; }

echo "Content-Type: application/json; charset=utf-8"
echo ""

urldecode() { : "${*//+/ }"; echo -e "${_//%/\\x}"; }
declare -A PARAM
parse_kv() {
    local kv_pair key val
    IFS='&' read -ra kv_pair <<< "$1"
    for pair in "${kv_pair[@]}"; do
        IFS='=' read -r key val <<< "${pair}"
        PARAM["$(urldecode "${key}")"]="$(urldecode "${val}")"
    done
}

case "$REQUEST_METHOD" in
POST)
    CONTENT_LENGTH=${CONTENT_LENGTH:-0}
    [ "$CONTENT_LENGTH" -gt 0 ] && read -r -n "$CONTENT_LENGTH" POST_DATA
    parse_kv "${POST_DATA}"
    ;;
GET)
    parse_kv "${QUERY_STRING}"
    ;;
*)
    log "Unsupported METHOD: ${REQUEST_METHOD}"
    echo '{"success":false,"message":"Unsupported METHOD","result":null}'
    exit 0
    ;;
esac

ACTION="${PARAM[action]}"
log "Request: ACTION=${ACTION}"

json_response() {
    local ok="$1" msg="$2" data="$3"
    local msg_json
    msg_json=$(echo "$msg" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))')
    if [ -z "$data" ]; then
        echo "{\"success\":$ok, \"message\":$msg_json, \"result\":null}"
    else
        echo "{\"success\":$ok, \"message\":$msg_json, \"result\":$data}"
    fi
}

case "${ACTION}" in
init)
    log "Web UI opened/refreshed"
    echo '{"success":true,"message":"init"}'
    ;;

getsettings)
    TARGET=$(synogetkeyvalue "$CONF_FILE" default_target 2>/dev/null)
    PORT=$(synogetkeyvalue "$CONF_FILE" default_port 2>/dev/null)
    [ -n "$PORT" ] || PORT=5201
    echo "{\"success\":true,\"default_target\":\"${TARGET}\",\"default_port\":${PORT}}"
    ;;

setsettings)
    synosetkeyvalue "$CONF_FILE" default_target "${PARAM[default_target]}"
    synosetkeyvalue "$CONF_FILE" default_port "${PARAM[default_port]:-5201}"
    echo '{"success":true}'
    ;;

*)
    log "[ERROR] Invalid action: ${ACTION}"
    json_response false "Invalid action: ${ACTION}" ""
    ;;
esac

exit 0
