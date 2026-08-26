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

verify_signed_request() {
    local action_str secret ts sig expected now
    action_str="$1"
    secret="$(synogetkeyvalue "$CONF_FILE" shared_secret 2>/dev/null)"
    [ -z "$secret" ] && return 1

    ts="${PARAM[ts]}"
    sig="${PARAM[sig]}"
    [[ "$ts" =~ ^[0-9]+$ ]] || return 1

    now=$(date +%s)
    (( now - ts > 60 || ts - now > 60 )) && return 1   # 60s replay window

    expected=$(printf '%s' "${action_str}|${ts}" | openssl dgst -sha256 -hmac "$secret" | awk '{print $2}')
    [[ "$sig" == "$expected" ]]
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
    SECRET=$(synogetkeyvalue "$CONF_FILE" shared_secret 2>/dev/null)
    [ -n "$PORT" ] || PORT=5201

    TARGET_JSON=$(printf '%s' "$TARGET" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    SECRET_JSON=$(printf '%s' "$SECRET" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

    echo "{\"success\":true,\"default_target\":${TARGET_JSON},\"default_port\":${PORT},\"shared_secret\":${SECRET_JSON}}"
    ;;

setsettings)
    NEW_TARGET="${PARAM[default_target]}"
    NEW_PORT="${PARAM[default_port]:-5201}"
    NEW_SECRET="${PARAM[shared_secret]}"

    if [[ -n "$NEW_TARGET" && ! "$NEW_TARGET" =~ ^[a-zA-Z0-9.-]+$ ]]; then
        json_response false "Invalid default target" ""
        exit 0
    fi
    if ! [[ "$NEW_PORT" =~ ^[0-9]+$ ]] || (( NEW_PORT < 1 || NEW_PORT > 65535 )); then
        json_response false "Invalid default port" ""
        exit 0
    fi
    if [[ "$NEW_SECRET" == *'"'* || "$NEW_SECRET" == *'\'* ]]; then
        json_response false "Shared secret cannot contain \\ or \"" ""
        exit 0
    fi

    NEW_SECRET="$(printf '%s' "$NEW_SECRET" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    synosetkeyvalue "$CONF_FILE" default_target "$NEW_TARGET"
    synosetkeyvalue "$CONF_FILE" default_port "$NEW_PORT"
    synosetkeyvalue "$CONF_FILE" shared_secret "$NEW_SECRET"

    # Read back what was actually stored - lets the UI confirm the save
    # matched what the user typed, immediately, rather than them only
    # noticing a difference later when reopening Settings.
    SAVED_TARGET=$(synogetkeyvalue "$CONF_FILE" default_target 2>/dev/null)
    SAVED_SECRET=$(synogetkeyvalue "$CONF_FILE" shared_secret 2>/dev/null)
    SAVED_TARGET_JSON=$(printf '%s' "$SAVED_TARGET" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    SAVED_SECRET_JSON=$(printf '%s' "$SAVED_SECRET" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')

    echo "{\"success\":true,\"saved_default_target\":${SAVED_TARGET_JSON},\"saved_shared_secret\":${SAVED_SECRET_JSON}}"
    ;;

startserver)
    port="${PARAM[port]:-5201}"
    if [[ ! "$port" =~ ^[0-9]+$ ]] || (( port < 1 || port > 65535 )); then
        json_response false "Invalid port" ""
        exit 0
    fi
    if ! verify_signed_request "startserver:${port}"; then
        json_response false "Unauthorized" ""
        exit 0
    fi

    LOG="${VAR_DIR}/server-${port}.log"
    nohup "${BIN_DIR}/syno_iperf3.sh" server-oneoff "$port" > "$LOG" 2>&1 < /dev/null &
    disown

    log "startserver: launched iperf3 -s -1 on port ${port} (pid $!, authenticated)"
    echo "{\"success\":true,\"port\":${port}}"
    ;;

remotestart)
    ip="${PARAM[ip]}"
    dsm_port="${PARAM[dsm_port]:-5001}"
    port="${PARAM[port]:-5201}"
    if [[ ! "$ip" =~ ^[a-zA-Z0-9.-]+$ ]]; then
        json_response false "Invalid ip" ""; exit 0
    fi
    secret="$(synogetkeyvalue "$CONF_FILE" shared_secret 2>/dev/null)"
    if [[ -z "$secret" ]]; then
        json_response false "No shared secret configured - set one in Settings on both NAS" ""
        exit 0
    fi
    ts=$(date +%s)
    sig=$(printf '%s' "startserver:${port}|${ts}" | openssl dgst -sha256 -hmac "$secret" | awk '{print $2}')
    resp=$(curl -sk --max-time 3 \
        "https://${ip}:${dsm_port}/webman/3rdparty/Synoiperf3/api.cgi?action=startserver&port=${port}&ts=${ts}&sig=${sig}" \
        2>>"${VAR_DIR}/api.log")
    if [ -z "$resp" ]; then
        resp='{"success":false,"message":"No response from remote NAS"}'
    fi
    echo "$resp"
    ;;

ping)
    pkgversion="$(synogetkeyvalue "${PKG_ROOT}"/INFO version)"
    echo "{\"success\":true,\"pkg\":\"Synoiperf3\",\"version\":\"${pkgversion}\"}"
    ;;

discover)
    NAS_LIST=$(python3 "${BIN_DIR}/syno_discover.py" --json --timeout 3 2>>"${VAR_DIR}/api.log")

    TMPDIR=$(mktemp -d)
    trap 'rm -rf "$TMPDIR"' EXIT

    i=0
    while IFS= read -r line; do
        ip=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('ip',''))" 2>/dev/null)
        hostname=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('hostname',''))" 2>/dev/null)
        https_port=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('https_port',5001))" 2>/dev/null)
        [ -z "$ip" ] && continue
        i=$((i+1))
        (
            resp=$(curl -sk --max-time 1 \
                "https://${ip}:${https_port}/webman/3rdparty/Synoiperf3/api.cgi?action=ping" 2>/dev/null)
            if echo "$resp" | grep -q '"pkg":"Synoiperf3"'; then
                echo "{\"ip\":\"${ip}\",\"hostname\":\"${hostname}\",\"dsm_port\":${https_port},\"port\":5201}" > "${TMPDIR}/${i}.json"
            fi
        ) &
    done < <(echo "$NAS_LIST" | python3 -c "
import json,sys
for n in json.load(sys.stdin):
    print(json.dumps(n))
")
    wait

    RESULTS=$(cat "${TMPDIR}"/*.json 2>/dev/null | python3 -c "
import json,sys
items = []
for line in sys.stdin:
    line = line.strip()
    if line:
        items.append(json.loads(line))
print(json.dumps(items))
")
    [ -z "$RESULTS" ] && RESULTS="[]"

    echo "{\"success\":true,\"result\":${RESULTS}}"
    ;;

internetservers)
    LIST_FILE="${BIN_DIR}/iperf3_internet_servers.json"
    if [ -f "$LIST_FILE" ]; then
        RESULT=$(cat "$LIST_FILE")
    else
        RESULT="[]"
    fi
    echo "{\"success\":true,\"result\":${RESULT}}"
    ;;

*)
    log "[ERROR] Invalid action: ${ACTION}"
    json_response false "Invalid action: ${ACTION}" ""
    ;;
esac

exit 0
