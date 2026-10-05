Mijia-720P-hack
================

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A comprehensive, cloud-free custom firmware modification for the **Xiaomi Mijia 720p 360° Smart Home Camera** (MJSXJ01CM, Grain Media GM8136S SoC).

![Mijia 720P Camera](mijia720p.png?raw=true "Mijia 720P camera")

---

## 🚀 Key Features

* **100% Cloud-Free & Private:** Blocks all telemetry and outbound traffic to Chinese servers.
* **Modern Web Dashboard:** Responsive mobile & desktop dark-mode dashboard running on the camera's built-in web server.
* **Full PTZ Motor Control:**
  * Virtual Touch D-Pad (Up, Down, Left, Right, Center).
  * Step size selector: 1x (Fine), 3x (Normal), 5x (Fast).
  * 4 Position Presets (Go to preset & Save current position).
  * Motor limit calibration sequence.
  * Keyboard arrow navigation (Arrow keys + Home key).
* **Hardware & Optics Controls:**
  * Night Vision mode (Auto via sensor / Always Day / Always Night).
  * Physical IR-Cut filter toggle.
  * IR LED illumination brightness slider (0–255 PWM).
  * Vertical flip (for ceiling mounts) & Horizontal mirror.
  * Status LEDs control (Blue & Yellow LEDs: On / Off / Blink).
* **Direct RTSP Video Stream:** H.264 video feed on standard port `554` (`rtsp://<ip>:554/live/ch00_0`).
* **Home Assistant Integration:** Pre-configured REST commands and Lovelace cards for full PTZ and stream control.
* **In-Browser Video Browser:** Browse, play, and download MP4 motion recordings directly in your browser.
* **Network Daemons:** Dropbear SSH (port 22), Telnet (port 23), Lighttpd HTTP (port 80), FTP (port 21), Samba/CIFS file share (port 445), NTP time sync.

---

## ⚠️ Disclaimer

> **CAUTION:** Many files on the internal flash of the Mijia 720P are writable. Always keep the SD card inserted while running the hack. Removing the SD card reboots the camera in its stock factory state. Do not overwrite firmware partitions.

---

## 💾 Installation

### 1. Requirements
* A MicroSD card (formatted as FAT32 / vfat, up to 32GB recommended).
* Xiaomi Mijia 720p 360° camera (model `MJSXJ01CM`).

### 2. SD Card Preparation
1. Format your MicroSD card with **FAT32**.
2. Copy the entire contents of the `sdcard/` folder directly to the root of your MicroSD card.
   Your SD card root should contain:
   ```
   ├── ft/
   ├── ft_config.ini
   ├── manufacture.bin
   ├── mijia-720p-hack/
   │   ├── bin/
   │   ├── etc/
   │   ├── scripts/
   │   └── www/
   └── mijia-720p-hack.cfg
   ```
3. Open `mijia-720p-hack.cfg` on your computer and configure your Wi-Fi credentials:
   ```sh
   WIFI_SSID="Your_WiFi_SSID"
   WIFI_PASS="Your_WiFi_Password"
   DISABLE_CLOUD=1      # Must be 1 for motor / PTZ control!
   ENABLE_RTSP=1        # Enable RTSP server
   ENABLE_HTTPD=1       # Enable Web server & REST API
   ENABLE_SSHD=1        # Enable SSH
   ```

### 3. Booting
1. Unplug the camera's power.
2. Insert the MicroSD card into the camera.
3. Power the camera on.
4. The LED indicates startup status:
   * **Yellow solid:** System boot.
   * **Blue blinking:** Connecting to Wi-Fi.
   * **Blue solid:** Wi-Fi connected! Motors will calibrate automatically.
5. Open `http://<your-camera-ip>/` in your browser.

---

## 🕹️ Web Dashboard & PTZ

The web interface is available at `http://<your-camera-ip>/`:

* **Dashboard (`/index.html`):** Virtual D-Pad for motor movement, coordinates display (Pan 0..31, Tilt 0..15), 4 position presets, night vision modes, IR LED slider, and real-time CPU/RAM/SD stats.
* **Settings (`/settings.html`):** Live configuration editor, WiFi manager, and Home Assistant YAML generator.
* **Recordings (`/recordings.html`):** Video file browser with built-in HTML5 playback and download.
* **About & Docs (`/about.html`):** System specs and REST API documentation.

---

## 🏠 Home Assistant Integration

### 1. `configuration.yaml`

Add the camera stream and REST commands for motor movement:

```yaml
camera:
  - platform: ffmpeg
    name: Mijia 720p
    input: -rtsp_transport tcp -i rtsp://<CAMERA_IP>:554/live/ch00_0

rest_command:
  # PTZ Motor Movement
  mijia_ptz_up:
    url: "http://<CAMERA_IP>/api/motor.php?action=move&dir=up&step=3"
    method: GET
  mijia_ptz_down:
    url: "http://<CAMERA_IP>/api/motor.php?action=move&dir=down&step=3"
    method: GET
  mijia_ptz_left:
    url: "http://<CAMERA_IP>/api/motor.php?action=move&dir=left&step=3"
    method: GET
  mijia_ptz_right:
    url: "http://<CAMERA_IP>/api/motor.php?action=move&dir=right&step=3"
    method: GET
  mijia_ptz_center:
    url: "http://<CAMERA_IP>/api/motor.php?action=center"
    method: GET
  mijia_ptz_calibrate:
    url: "http://<CAMERA_IP>/api/motor.php?action=calibrate"
    method: GET

  # Position Presets
  mijia_preset_1:
    url: "http://<CAMERA_IP>/api/motor.php?action=preset&id=1"
    method: GET
  mijia_preset_2:
    url: "http://<CAMERA_IP>/api/motor.php?action=preset&id=2"
    method: GET

  # Optics & IR
  mijia_night_mode_auto:
    url: "http://<CAMERA_IP>/api/camera.php?action=night_mode&mode=auto"
    method: GET
  mijia_night_mode_off:
    url: "http://<CAMERA_IP>/api/camera.php?action=night_mode&mode=off"
    method: GET
  mijia_night_mode_on:
    url: "http://<CAMERA_IP>/api/camera.php?action=night_mode&mode=on"
    method: GET
```

### 2. Lovelace Card with PTZ Controls

Create a Lovelace card with PTZ buttons superimposed on the camera feed:

```yaml
type: picture-elements
camera_image: camera.mijia_720p
camera_view: live
elements:
  - type: icon
    icon: mdi:arrow-up-bold
    style:
      top: 15%
      left: 50%
    tap_action:
      action: call-service
      service: rest_command.mijia_ptz_up

  - type: icon
    icon: mdi:arrow-down-bold
    style:
      top: 85%
      left: 50%
    tap_action:
      action: call-service
      service: rest_command.mijia_ptz_down

  - type: icon
    icon: mdi:arrow-left-bold
    style:
      top: 50%
      left: 10%
    tap_action:
      action: call-service
      service: rest_command.mijia_ptz_left

  - type: icon
    icon: mdi:arrow-right-bold
    style:
      top: 50%
      left: 90%
    tap_action:
      action: call-service
      service: rest_command.mijia_ptz_right

  - type: icon
    icon: mdi:image-filter-center-focus
    style:
      top: 50%
      left: 50%
    tap_action:
      action: call-service
      service: rest_command.mijia_ptz_center
```

---

## 📡 REST API Reference

All endpoints accept both `GET` and `POST` requests and return JSON:

### 1. PTZ Motor Control (`/api/motor.php` or `/api/motor.cgi`)
| Parameter | Values | Description |
|---|---|---|
| `action=status` | - | Returns current motor coordinates `{ horizontal: { x, HPOS }, vertical: { y, VPOS } }` |
| `action=move` | `dir=up\|down\|left\|right`, `step=1..15` | Move motor relative steps |
| `action=goto` | `x=0..31`, `y=0..15` | Move to absolute coordinate |
| `action=center` | - | Center camera at `(16, 7)` |
| `action=calibrate` | - | Sweep end-to-end and calibrate motors |
| `action=preset` | `id=1..4` | Move to preset position |
| `action=set_preset` | `id=1..4` | Save current position as preset |
| `action=get_presets` | - | Returns coordinates of all presets |

### 2. Camera & Hardware Control (`/api/camera.php` or `/api/camera.cgi`)
| Parameter | Values | Description |
|---|---|---|
| `action=status` | - | Returns night vision, IR LED, IR-cut, flip, mirror, and LED states |
| `action=night_mode` | `mode=auto\|on\|off` | Switch night vision mode |
| `action=ir_led` | `value=0..255\|on\|off` | Set infrared illuminator brightness |
| `action=ir_cut` | `state=on\|off` | Toggle mechanical IR-blocking filter |
| `action=flip` | `state=on\|off` | Vertical image flip (ceiling mount) |
| `action=mirror` | `state=on\|off` | Horizontal image mirror |
| `action=led` | `color=blue\|yellow`, `state=on\|off\|blink` | Front status LED control |

### 3. System & Services (`/api/system.php`)
| Parameter | Values | Description |
|---|---|---|
| `action=info` | - | System load, uptime, RAM memory, SD card usage, WiFi signal, and services |
| `action=reboot` | - | Reboot the camera |
| `action=service` | `name=<service>`, `cmd=start\|stop\|restart` | Manage service (`rtsp`, `ssh`, `ftp`, `samba`, `cloud`) |

### 4. Settings Configuration (`/api/settings.php`)
* `GET /api/settings.php`: Read configuration from `mijia-720p-hack.cfg`.
* `POST /api/settings.php`: Save updated configuration (WiFi, passwords, timezones, service switches).

---

## 🛠️ Network Services

* **RTSP Server:** Port `554` (`rtsp://<ip>:554/live/ch00_0`)
* **SSH Server (Dropbear):** Port `22` (User: `root`, Password: configured in `.cfg`)
* **Telnet Server:** Port `23` (User: `root`)
* **Web Server (Lighttpd):** Port `80`
* **FTP Server:** Port `21` (Anonymous access to `/tmp/sd`)
* **Samba (CIFS):** Port `445` (`\\<ip>\MIJIA_RECORD_VIDEO`)

---

## 🏗️ Building from Source

To compile the binaries with the GM8136 SDK toolchain:
```sh
cd mijia-720p-hack
make
make install
```

---

## 📜 Credits & License

* Originally created by [Jan Sperling (ghoost82)](https://github.com/ghoost82/mijia-720p-hack).
* Enhanced by [Buktahula](https://github.com/Buktahula/mijia-720p-hack) and the open source community.
* Licensed under **GPLv3**.
