#!/bin/sh
echo "Content-Type: application/json; charset=utf-8"
echo "Access-Control-Allow-Origin: *"
echo ""

sd_mountdir="/tmp/sd"
if [ -r "${sd_mountdir}/mijia-720p-hack/scripts/functions.sh" ]; then
  . "${sd_mountdir}/mijia-720p-hack/scripts/functions.sh" >/dev/null 2>&1
fi

eval $(echo "$QUERY_STRING" | awk -F'&' '{for(i=1;i<=NF;i++){print $i}}' | grep '=' | sed 's/\([^=]*\)=\(.*\)/PARAM_\1="\2"/')

action="${PARAM_action:-status}"

case "${action}" in
  night_mode)
    mode="${PARAM_mode:-auto}"
    night_mode "${mode}" >/dev/null 2>&1
    night_mode status
    ;;
  ir_led)
    val="${PARAM_value:-0}"
    ir_led "${val}" >/dev/null 2>&1
    ir_led status
    ;;
  ir_cut)
    state="${PARAM_state:-on}"
    ir_cut "${state}" >/dev/null 2>&1
    ir_cut status
    ;;
  flip)
    state="${PARAM_state:-off}"
    flip "${state}" >/dev/null 2>&1
    flip status
    ;;
  mirror)
    state="${PARAM_state:-off}"
    mirror "${state}" >/dev/null 2>&1
    mirror status
    ;;
  led)
    col="${PARAM_color:-blue}"
    st="${PARAM_state:-off}"
    if [ "${col}" = "blue" ]; then
      blue_led "${st}" >/dev/null 2>&1
      blue_led status
    else
      yellow_led "${st}" >/dev/null 2>&1
      yellow_led status
    fi
    ;;
  status|*)
    nm="$(night_mode status)"
    irled="$(ir_led status)"
    ircut="$(ir_cut status)"
    fl="$(flip status)"
    mr="$(mirror status)"
    bl="$(blue_led status)"
    yl="$(yellow_led status)"
    cat << EOF
{
  "camera": {
    "night_mode": ${nm},
    "ir_led": ${irled},
    "ir_cut": ${ircut},
    "flip": ${fl},
    "mirror": ${mr},
    "blue_led": ${bl},
    "yellow_led": ${yl}
  }
}
EOF
    ;;
esac
