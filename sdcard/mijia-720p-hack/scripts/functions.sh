#!/bin/sh

## purpose: some basic functions
## license: GPLv3+, http://www.gnu.org/licenses/gpl-3.0.html
## author: Jan Sperling, 2018

sd_mountdir="/tmp/sd"
LOGDIR="${sd_mountdir}/log"
BASECFG="${sd_mountdir}/mijia-720p-hack.cfg"
MIJIACTRL="${sd_mountdir}/mijia-720p-hack/bin/mijia_ctrl"
if [ -f "${BASECFG}" ]; then
  . "${BASECFG}"
fi

# Creates /tmp/disable-binary
create_disable_binary() {
    if [ ! -f /tmp/disable-binary ]; then
    cat > /tmp/disable-binary << EOF
#!/bin/sh
echo "\$0 disabled with mijia-720p-hack"
EOF
    chmod +x /tmp/disable-binary
  fi
}

# Disable binary and optionally delete it from restartd.conf
disable_binary() {
  binary="$1"
  restart="$2"
  create_disable_binary
  echo "Disabling ${1##*/}"
  if pgrep "${binary}" >/dev/null; then
    pkill "${binary}"
  fi
  if ! mount | grep -q "${binary}"; then
    mount --bind /tmp/disable-binary "${binary}"
  fi
  # update restartd.conf
  if [ -n "${restart}" ] &&
     [ -f /tmp/etc/restartd.conf ] &&
     grep -q ^"${restart} " /tmp/etc/restartd.conf; then
    sed -i "/^${restart} /d" /tmp/etc/restartd.conf
  fi
}

# Enable binary and optionally add it to restartd.conf
enable_binary() {
  binary="$1"
  restart="$2"
  if mount|grep -q "${binary}"; then
    umount "${binary}"
  fi
  # update restartd.conf
  if [ -n "${restart}" ] &&
     [ -f /tmp/etc/restartd.conf ] &&
     ! grep -q ^"${restart} " /tmp/etc/restartd.conf; then
    grep ^"${restart} " /tmp/etc/restartd.conf.org >> /tmp/etc/restartd.conf
  fi
}

# Print start-stop-daemon return status
ok_fail() {
  if [ "$1" = 0 ]; then
    echo "OK" 
  else
    echo "FAIL"
  fi
}

# Start daemon
start_daemon() {
  echo "Starting ${DESC}"
  start-stop-daemon --start --quiet --oknodo \
                    --exec "${DAEMON}" -- ${DAEMON_OPTS}
  RC="$?"
  ok_fail "${RC}"
  return "${RC}"
}

# Start a process as background daemon
start_daemon_background() {
  echo "Starting ${DESC}"
  start-stop-daemon --start --quiet --oknodo \
                    --pidfile "${PIDFILE}" --make-pidfile --background \
                    --exec "${DAEMON}" -- ${DAEMON_OPTS}
  RC="$?"
  ok_fail "${RC}"
  return "${RC}"
}

# Stop daemon
stop_daemon() {
  echo "Stopping ${DESC}"
  start-stop-daemon --stop --quiet --oknodo \
                    --pidfile "${PIDFILE}"
  RC="$?"
  ok_fail "${RC}"
  return "${RC}"
}

# Stop background daemon
stop_daemon_background() {
  if stop_daemon; then 
    if [ -f "${PIDFILE}" ]; then
      rm "${PIDFILE}"
    fi
  fi
  return "${RC}"
}

# Status of a daemon
status_daemon() {
  pid="$(cat "${PIDFILE}" 2>/dev/null)"
  if [ "${pid}" ]; then
    if kill -0 "${pid}" >/dev/null 2>/dev/null; then
      echo "${DESC} is running with PID: ${pid}"
      RC="0"
    else
      echo "${DESC} is dead"
      RC="1"
    fi
  else
    echo "${DESC} is not running"
    RC="3"
  fi
  return "${RC}"
}

# Check for daemon executable
check_daemon_bin() {
  binary="$1"
  description="$2"
  if [ ! -x "${binary}" ]; then
    echo "Could not find ${description} binary"
    exit 1
  fi
}

# get NVRAM variable
get_nvram() {
  variable="$1"
  /usr/sbin/nvram get "${variable}" | xargs
}

# Save NVRAM variable
set_nvram() {
  variable="$1"
  value="$2"
  if [ "$(get_nvram "${variable}")" != "${value}" ]; then
    /usr/sbin/nvram set ${variable}="${value}"; RC="$((RC|$?))"
    /usr/sbin/nvram commit; RC="$((RC|$?))"
  fi
  return "${RC}"
}

# Get ISP328 values 
get_isp328() {
  variable="$1"
  echo r ${variable} > /proc/isp328/command
  cat /proc/isp328/command
}

# Set ISP328 values 
set_isp328() {
  variable="$1"
  value="$2"
  echo w ${variable} ${value} > /proc/isp328/command; RC="$((RC|$?))"
  return "${RC}"
}

# Read a value from a GPIO pin
get_gpio(){
  pin="$1"
  cat /sys/class/gpio/gpio${pin}/value
}

# Write a value to GPIO pin
set_gpio() {
  pin="$1"
  value="$2"
  echo "${value}" > /sys/class/gpio/gpio${pin}/value; RC="$((RC|$?))"
  return "${RC}"
}

# Set config value in basecfg
set_basecfg() {
  variable="$1"
  value="$2"
  if egrep -q "^[[:space:]]*${variable}=(|\")${value}(|\"[[:space:]]*)$" "${BASECFG}"; then
    RC="0"
  elif grep -q "^[[:space:]]*${variable}=" "${BASECFG}"; then
    sed -i -e "/^[[:space:]]*${variable}=/ s/=.*/=\"${value}\"/" "${BASECFG}"; RC="$((RC|$?))"
  else
    echo "${variable}=\"${value}\"" >> "${BASECFG}"; RC="$((RC|$?))"
  fi
  return "${RC}"
}

# Control the blue LED
blue_led(){
  case "$1" in
    on)
      /mnt/data/miot/ledctl 0 50 0 0 0 2 > /dev/null 2>&1; RC="$((RC|$?))"
      echo "on" > /var/run/blue_led
      ;;
    off)
      /mnt/data/miot/ledctl 0 50 1 0 0 2 > /dev/null 2>&1; RC="$((RC|$?))"
      echo "off" > /var/run/blue_led
      ;;
    blink)
      /mnt/data/miot/ledctl 0 50 2 0 0 2 > /dev/null 2>&1; RC="$((RC|$?))"
      echo "blink" > /var/run/blue_led
      ;;
    status)
      val="$(cat /var/run/blue_led 2>/dev/null || echo "off")"
      cat << EOF
{
  "blue_led": "${val}"
}
EOF
      RC="0"
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

# Control the yellow LED
yellow_led(){
  case "$1" in
    on)
      /mnt/data/miot/ledctl 1 50 0 0 0 2 > /dev/null 2>&1; RC="$((RC|$?))"
      echo "on" > /var/run/yellow_led
      ;;
    off)
      /mnt/data/miot/ledctl 1 50 1 0 0 2 > /dev/null 2>&1; RC="$((RC|$?))"
      echo "off" > /var/run/yellow_led
      ;;
    blink)
      /mnt/data/miot/ledctl 1 50 2 0 0 2 > /dev/null 2>&1; RC="$((RC|$?))"
      echo "blink" > /var/run/yellow_led
      ;;
    status)
      val="$(cat /var/run/yellow_led 2>/dev/null || echo "off")"
      cat << EOF
{
  "yellow_led": "${val}"
}
EOF
      RC="0"
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

# Control the infrared LED
ir_led(){
  if ! [ -x "${MIJIACTRL}" ]; then
    echo "could not find ${MIJIACTRL}"
    return 1
  fi
  case "$1" in
    on)
      ${MIJIACTRL} IRLED 255 > /dev/null; RC="$((RC|$?))"
      echo 255 > /var/run/irled
      ;;
    off)
      ${MIJIACTRL} IRLED 0 > /dev/null; RC="$((RC|$?))"
      echo 0 > /var/run/irled
      ;;
    status)
      val="$(cat /var/run/irled 2>/dev/null || echo 0)"
      cat << EOF
{
  "ir_led": "${val}"
}
EOF
      RC="0"
      ;;
    [0-9]*)
      val="$1"
      if [ "${val}" -gt 255 ]; then val=255; fi
      if [ "${val}" -lt 0 ]; then val=0; fi
      ${MIJIACTRL} IRLED "${val}" > /dev/null; RC="$((RC|$?))"
      echo "${val}" > /var/run/irled
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

# Control the infrared filter
ir_cut(){
  case "$1" in
    on)
      set_gpio 14 1; RC="$((RC|$?))"
      set_gpio 15 0; RC="$((RC|$?))"
      echo 1 > /var/run/ircut
      ;;
    off)
      set_gpio 14 0; RC="$((RC|$?))"
      set_gpio 15 1; RC="$((RC|$?))"
      echo 0 > /var/run/ircut
      ;;
    status)
      status="$(cat /var/run/ircut 2>/dev/null || get_gpio 14)"
      cat << EOF
{
  "ir_cut": "${status}"
}
EOF
      if [ -n "${status}" ]; then
        RC="0"
      else
        RC="1"
      fi
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

# Control the night mode
night_mode(){
  case "$1" in
    on)
      if [ -x "${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode" ]; then
        ${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode stop > /dev/null 2>&1
      fi
      ir_led on; RC="$((RC|$?))"
      ir_cut off; RC="$((RC|$?))"
      set_isp328 daynight 1; RC="$((RC|$?))"
      set_nvram night_mode 2; RC="$((RC|$?))"
      ;;
    off)
      if [ -x "${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode" ]; then
        ${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode stop > /dev/null 2>&1
      fi
      ir_led off; RC="$((RC|$?))"
      ir_cut on; RC="$((RC|$?))"
      set_isp328 daynight 0; RC="$((RC|$?))"
      set_nvram night_mode 1; RC="$((RC|$?))"
      ;;
    auto)
      if [ -x "${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode" ]; then
        ${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode start > /dev/null 2>&1
      fi
      set_nvram night_mode 0; RC="$((RC|$?))"
      ;;
    status)
      nv="$(get_nvram night_mode)"
      status="$(get_isp328 daynight)"
      auto="off"
      if pgrep ir_sample > /dev/null 2>&1; then
        auto="on"
      fi
      cat << EOF
{
  "night_mode": "${status}",
  "nvram": "${nv}",
  "auto": "${auto}"
}
EOF
      RC="0"
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

# Controll flip mode
flip() {
  case "$1" in
    on)
      set_isp328 flip 1; RC="$((RC|$?))"
      ;;
    off)
      set_isp328 flip 0; RC="$((RC|$?))"
      ;;
    status)
      status="$(get_isp328 flip)"
      cat << EOF
{
  "flip": "${status}"
}
EOF
      if [ -n "${status}" ]; then
        RC="0"
      else
        RC="1"
      fi
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

# Controll mirror mode
mirror() {
  case "$1" in
    on)
      set_isp328 mirror 1; RC="$((RC|$?))"
      ;;
    off)
      set_isp328 mirror 0; RC="$((RC|$?))"
      ;;
    status)
      status="$(get_isp328 mirror)"
      cat << EOF
{
  "mirror": "${status}"
}
EOF
      if [ -n "${status}" ]; then
        RC="0"
      else
        RC="1"
      fi
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac
  return "${RC}"
}

PRESETS_FILE="${sd_mountdir}/mijia-720p-hack/etc/presets.conf"

get_preset() {
  id="$1"
  if [ -f "${PRESETS_FILE}" ]; then
    grep "^PRESET_${id}=" "${PRESETS_FILE}" | cut -d'=' -f2 | tr -d '"'
  fi
}

set_preset_pos() {
  id="$1"
  pos="$2"
  mkdir -p "${sd_mountdir}/mijia-720p-hack/etc"
  if [ ! -f "${PRESETS_FILE}" ]; then
    cat > "${PRESETS_FILE}" << 'EOF'
PRESET_1="16 7"
PRESET_2="0 7"
PRESET_3="31 7"
PRESET_4="16 0"
EOF
  fi
  if grep -q "^PRESET_${id}=" "${PRESETS_FILE}"; then
    sed -i "s/^PRESET_${id}=.*/PRESET_${id}=\"${pos}\"/" "${PRESETS_FILE}"
  else
    echo "PRESET_${id}=\"${pos}\"" >> "${PRESETS_FILE}"
  fi
}

# Calibrate and control the motor
motor(){
  if ! [ -x "${MIJIACTRL}" ]; then
    echo "could not find ${MIJIACTRL}"
    return 1
  fi
  # Motor will not move if PWM is in use
  if [ "${DISABLE_CLOUD}" -eq 0 ]; then
    echo "motor only supported while cloud is disabled"
    return 1
  elif [ "$1" = "up" ] || [ "$1" = "down" ] ||
       [ "$1" = "left" ] || [ "$1" = "right" ] || 
       [ "$1" = "calibrate" ] || [ "$1" = "goto" ] ||
       [ "$1" = "center" ] || [ "$1" = "preset" ]; then
    if [ -x "${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode" ]; then
      ${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode stop > /dev/null 2>&1
    fi
  fi

  ptz_x="$(get_nvram ptz-x)"
  ptz_y="$(get_nvram ptz-y)"
  case "${ptz_x}" in
    ''|*[!0-9]*) ptz_x=16 ;;
  esac
  case "${ptz_y}" in
    ''|*[!0-9]*) ptz_y=7 ;;
  esac

  if [ "${ptz_y}" -gt 15 ]; then
    set_nvram ptz-y 15; RC="$((RC|$?))"
    ptz_y=15
  fi
  if [ "${ptz_y}" -lt 0 ]; then
    set_nvram ptz-y 0; RC="$((RC|$?))"
    ptz_y=0
  fi
  if [ "${ptz_x}" -gt 31 ]; then
    set_nvram ptz-x 31; RC="$((RC|$?))"
    ptz_x=31
  fi
  if [ "${ptz_x}" -lt 0 ]; then
    set_nvram ptz-x 0; RC="$((RC|$?))"
    ptz_x=0
  fi

  step="${2:-1}"
  case "${step}" in
    ''|*[!0-9]*) step=1 ;;
  esac
  if [ "${step}" -lt 1 ]; then step=1; fi

  case "$1" in
    up)
      new_y=$((ptz_y + step))
      if [ "${new_y}" -gt 15 ]; then new_y=15; fi
      dy=$((new_y - ptz_y))
      if [ "${dy}" -gt 0 ]; then
        ${MIJIACTRL} MOVE 0 +${dy} > /dev/null; RC="$((RC|$?))"
        set_nvram ptz-y "${new_y}"; RC="$((RC|$?))"
        ptz_y="${new_y}"
      fi
      ;;
    down)
      new_y=$((ptz_y - step))
      if [ "${new_y}" -lt 0 ]; then new_y=0; fi
      dy=$((ptz_y - new_y))
      if [ "${dy}" -gt 0 ]; then
        ${MIJIACTRL} MOVE 0 -${dy} > /dev/null; RC="$((RC|$?))"
        set_nvram ptz-y "${new_y}"; RC="$((RC|$?))"
        ptz_y="${new_y}"
      fi
      ;;
    left)
      new_x=$((ptz_x + step))
      if [ "${new_x}" -gt 31 ]; then new_x=31; fi
      dx=$((new_x - ptz_x))
      if [ "${dx}" -gt 0 ]; then
        ${MIJIACTRL} MOVE +${dx} 0 > /dev/null; RC="$((RC|$?))"
        set_nvram ptz-x "${new_x}"; RC="$((RC|$?))"
        ptz_x="${new_x}"
      fi
      ;;
    right)
      new_x=$((ptz_x - step))
      if [ "${new_x}" -lt 0 ]; then new_x=0; fi
      dx=$((ptz_x - new_x))
      if [ "${dx}" -gt 0 ]; then
        ${MIJIACTRL} MOVE -${dx} 0 > /dev/null; RC="$((RC|$?))"
        set_nvram ptz-x "${new_x}"; RC="$((RC|$?))"
        ptz_x="${new_x}"
      fi
      ;;
    goto)
      tgt_x="$2"
      tgt_y="$3"
      case "${tgt_x}" in ''|*[!0-9]*) tgt_x=${ptz_x} ;; esac
      case "${tgt_y}" in ''|*[!0-9]*) tgt_y=${ptz_y} ;; esac
      if [ "${tgt_x}" -gt 31 ]; then tgt_x=31; fi
      if [ "${tgt_x}" -lt 0 ]; then tgt_x=0; fi
      if [ "${tgt_y}" -gt 15 ]; then tgt_y=15; fi
      if [ "${tgt_y}" -lt 0 ]; then tgt_y=0; fi
      dx=$((tgt_x - ptz_x))
      dy=$((tgt_y - ptz_y))
      cmd_x="0"
      cmd_y="0"
      if [ "${dx}" -gt 0 ]; then cmd_x="+${dx}"; elif [ "${dx}" -lt 0 ]; then cmd_x="${dx}"; fi
      if [ "${dy}" -gt 0 ]; then cmd_y="+${dy}"; elif [ "${dy}" -lt 0 ]; then cmd_y="${dy}"; fi
      ${MIJIACTRL} MOVE "${cmd_x}" "${cmd_y}" > /dev/null; RC="$((RC|$?))"
      set_nvram ptz-x "${tgt_x}"; RC="$((RC|$?))"
      set_nvram ptz-y "${tgt_y}"; RC="$((RC|$?))"
      ptz_x="${tgt_x}"
      ptz_y="${tgt_y}"
      ;;
    center)
      motor goto 16 7
      ;;
    preset)
      p_id="$2"
      pos="$(get_preset "${p_id}")"
      if [ -n "${pos}" ]; then
        px="$(echo "${pos}" | awk '{print $1}')"
        py="$(echo "${pos}" | awk '{print $2}')"
        motor goto "${px}" "${py}"
      fi
      ;;
    set_preset)
      p_id="$2"
      set_preset_pos "${p_id}" "${ptz_x} ${ptz_y}"
      echo "Preset ${p_id} saved: ${ptz_x} ${ptz_y}"
      ;;
    get_presets)
      p1="$(get_preset 1)"; p1="${p1:-16 7}"
      p2="$(get_preset 2)"; p2="${p2:-0 7}"
      p3="$(get_preset 3)"; p3="${p3:-31 7}"
      p4="$(get_preset 4)"; p4="${p4:-16 0}"
      cat << EOF
{
  "preset_1": { "x": $(echo "${p1}" | awk '{print $1}'), "y": $(echo "${p1}" | awk '{print $2}') },
  "preset_2": { "x": $(echo "${p2}" | awk '{print $1}'), "y": $(echo "${p2}" | awk '{print $2}') },
  "preset_3": { "x": $(echo "${p3}" | awk '{print $1}'), "y": $(echo "${p3}" | awk '{print $2}') },
  "preset_4": { "x": $(echo "${p4}" | awk '{print $1}'), "y": $(echo "${p4}" | awk '{print $2}') }
}
EOF
      RC="0"
      ;;
    calibrate)
      ${MIJIACTRL} MOVE +31 +15 > /dev/null; RC="$((RC|$?))"
      sleep 2
      ${MIJIACTRL} MOVE -31 -15 > /dev/null; RC="$((RC|$?))"
      sleep 2
      ${MIJIACTRL} MOVE +"${ptz_x}" +"${ptz_y}" > /dev/null; RC="$((RC|$?))"
      sleep 2
      ;;
    status)
      status="$(${MIJIACTRL} MOVE 0 0  2> /dev/null | tr ',' '\n')"
      vpos="$(echo "${status}" | awk -F'=' '/VPOS/ {print $2}')"
      hpos="$(echo "${status}" | awk -F'=' '/HPOS/ {print $2}')"
      cat << EOF
{
  "motor":
  { "horizontal": 
    { "x": ${ptz_x},
      "HPOS": "${hpos}"
    },
    "vertical":
    {
      "y": ${ptz_y},
      "VPOS": "${vpos}"
    }
  }
}
EOF
      if [ -n "${ptz_x}" ] && [ -n "${ptz_y}" ]; then
        RC="0"
      else
        RC="1"
      fi
      ;;
    *)
      echo "Option $1 not supported"
      RC="1"
      ;;
  esac

  #Restart auto_night_mode if necessary
  if [ "$1" = "up" ] || [ "$1" = "down" ] ||
     [ "$1" = "left" ] || [ "$1" = "right" ] ||
     [ "$1" = "calibrate" ] || [ "$1" = "goto" ] ||
     [ "$1" = "center" ] || [ "$1" = "preset" ]; then
    if [ "$(get_nvram night_mode)" = "0" ] && [ -x "${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode" ]; then
      ${sd_mountdir}/mijia-720p-hack/scripts/S99auto_night_mode start > /dev/null 2>&1; RC="$((RC|$?))"
    fi
  fi
  return "${RC}"
}

# Get system status as JSON
system_status() {
  uptime_str="$(uptime 2>/dev/null)"
  loadavg="$(cat /proc/loadavg 2>/dev/null | awk '{print $1" "$2" "$3}')"
  
  # Memory in KB
  mem_total="$(awk '/MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null)"
  mem_free="$(awk '/MemFree:/ {print $2}' /proc/meminfo 2>/dev/null)"
  mem_buffers="$(awk '/Buffers:/ {print $2}' /proc/meminfo 2>/dev/null)"
  mem_cached="$(awk '/^Cached:/ {print $2}' /proc/meminfo 2>/dev/null)"
  mem_used=$((mem_total - mem_free - mem_buffers - mem_cached))
  if [ "${mem_used}" -lt 0 ] 2>/dev/null; then mem_used=$((mem_total - mem_free)); fi

  # Storage in KB
  sd_total="$(df /tmp/sd 2>/dev/null | awk 'NR==2 {print $2}')"
  sd_used="$(df /tmp/sd 2>/dev/null | awk 'NR==2 {print $3}')"
  sd_free="$(df /tmp/sd 2>/dev/null | awk 'NR==2 {print $4}')"

  # Network
  ip_addr="$(ip -4 addr show dev wlan0 2>/dev/null | awk '/inet / {print $2}' | cut -d'/' -f1)"
  if [ -z "${ip_addr}" ]; then
    ip_addr="$(ifconfig wlan0 2>/dev/null | awk '/inet addr:/ {print $2}' | cut -d':' -f2)"
  fi
  wifi_ssid="$(get_nvram miio_ssid)"
  wifi_signal="$(cat /proc/net/wireless 2>/dev/null | awk 'NR==3 {print $3}' | tr -d '.')"

  # Service statuses
  srv_rtsp="stopped"; if pgrep rtspd >/dev/null 2>&1; then srv_rtsp="running"; fi
  srv_http="stopped"; if pgrep lighttpd >/dev/null 2>&1; then srv_http="running"; fi
  srv_ssh="stopped"; if pgrep dropbear >/dev/null 2>&1; then srv_ssh="running"; fi
  srv_telnet="stopped"; if pgrep telnetd >/dev/null 2>&1; then srv_telnet="running"; fi
  srv_ftp="stopped"; if pgrep tcpsvd >/dev/null 2>&1 || pgrep ftpd >/dev/null 2>&1; then srv_ftp="running"; fi
  srv_samba="stopped"; if pgrep smbd >/dev/null 2>&1; then srv_samba="running"; fi
  srv_cloud="disabled"; if pgrep miio_avstreamer >/dev/null 2>&1; then srv_cloud="enabled"; fi
  srv_auto_night="stopped"; if pgrep ir_sample >/dev/null 2>&1; then srv_auto_night="running"; fi

  cat << EOF
{
  "system": {
    "uptime": "${uptime_str}",
    "loadavg": "${loadavg}",
    "memory": {
      "total_kb": ${mem_total:-0},
      "used_kb": ${mem_used:-0},
      "free_kb": ${mem_free:-0}
    },
    "sdcard": {
      "total_kb": ${sd_total:-0},
      "used_kb": ${sd_used:-0},
      "free_kb": ${sd_free:-0}
    },
    "network": {
      "ip": "${ip_addr}",
      "ssid": "${wifi_ssid}",
      "signal": "${wifi_signal:-0}"
    },
    "services": {
      "rtsp": "${srv_rtsp}",
      "http": "${srv_http}",
      "ssh": "${srv_ssh}",
      "telnet": "${srv_telnet}",
      "ftp": "${srv_ftp}",
      "samba": "${srv_samba}",
      "cloud": "${srv_cloud}",
      "auto_night_mode": "${srv_auto_night}"
    }
  }
}
EOF
}

if [ ! -d /var/run ]; then 
  mkdir -p /var/run 
fi 

