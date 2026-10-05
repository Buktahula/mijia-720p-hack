#!/bin/sh
echo "Content-Type: application/json; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
echo ""

sd_mountdir="/tmp/sd"
if [ -r "${sd_mountdir}/mijia-720p-hack/scripts/functions.sh" ]; then
  . "${sd_mountdir}/mijia-720p-hack/scripts/functions.sh" >/dev/null 2>&1
fi

# Parse query parameters from QUERY_STRING
eval $(echo "$QUERY_STRING" | awk -F'&' '{for(i=1;i<=NF;i++){print $i}}' | grep '=' | sed 's/\([^=]*\)=\(.*\)/PARAM_\1="\2"/')

action="${PARAM_action:-status}"

case "${action}" in
  move)
    dir="${PARAM_dir:-up}"
    step="${PARAM_step:-1}"
    motor "${dir}" "${step}" >/dev/null 2>&1
    motor status
    ;;
  goto)
    x="${PARAM_x:-16}"
    y="${PARAM_y:-7}"
    motor goto "${x}" "${y}" >/dev/null 2>&1
    motor status
    ;;
  center)
    motor center >/dev/null 2>&1
    motor status
    ;;
  calibrate)
    motor calibrate >/dev/null 2>&1
    motor status
    ;;
  preset)
    id="${PARAM_id:-1}"
    motor preset "${id}" >/dev/null 2>&1
    motor status
    ;;
  set_preset)
    id="${PARAM_id:-1}"
    motor set_preset "${id}"
    ;;
  presets)
    motor get_presets
    ;;
  status|*)
    motor status
    ;;
esac
