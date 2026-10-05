# Home Assistant Integration for Xiaomi Mijia 720p (Hacked)

This folder contains the complete, **zero-YAML** Home Assistant integration and Lovelace UI card for the hacked Xiaomi Mijia 720p 360° camera.

---

## 🌟 What's Included

1. **Custom Component (`custom_components/mijia_720p/`):**
   * **UI Config Flow:** Install and configure directly in Home Assistant (Settings → Devices & Services) without touching `configuration.yaml`.
   * **Camera Entity:** Real-time H.264 RTSP video stream with thumbnail snapshot support.
   * **PTZ Control Buttons:** Up, Down, Left, Right, Center, and Calibrate.
   * **Preset Buttons:** Presets 1–4 (Go To & Save).
   * **Night Vision Select:** Auto / Always Day / Always Night.
   * **IR LED Number Slider:** 0 to 255 PWM brightness control.
   * **Hardware Switches:** IR-Cut filter, Ceiling Vertical Flip, Horizontal Mirror, Blue LED, Yellow LED.
   * **Diagnostic Sensors:** Current Pan/Tilt coordinates, CPU Load, RAM usage, SD card free space, and Wi-Fi signal.
   * **System Button:** Reboot Camera.

2. **Custom Lovelace Card (`www/mijia-ptz-card.js`):**
   * Superimposes a touch D-Pad and preset buttons over the live camera stream.
   * Variable step size selector (1x Fine, 3x Normal, 5x Fast).
   * Visual GUI Card Editor in Home Assistant dashboard.
   * Can work directly with the `mijia_720p` integration or standalone via the camera's IP!

---

## 🚀 Easy Installation (Zero-YAML)

### Step 1: Install the Custom Integration

1. Copy the `custom_components/mijia_720p` directory into your Home Assistant's `/config/custom_components/` folder:
   ```sh
   # Path in Home Assistant:
   /config/custom_components/mijia_720p/
   ```
2. Restart Home Assistant (**Developer Tools → Restart** or **Settings → System → Restart**).
3. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
4. Search for **Xiaomi Mijia 720p (Hacked)**.
5. Enter your camera's IP address (e.g. `192.168.1.120`) and submit.
6. All camera entities, buttons, switches, and sensors are added instantly!

---

### Step 2: Install the Lovelace PTZ Card

1. Copy `www/mijia-ptz-card.js` into your Home Assistant `/config/www/` folder.
2. In Home Assistant, go to **Settings → Dashboards → Three dots (top right) → Resources**.
3. Click **Add Resource**:
   * **URL:** `/local/mijia-ptz-card.js`
   * **Resource Type:** `JavaScript Module`
4. Refresh your browser page.
5. In your Lovelace dashboard, click **Add Card** and choose **Mijia 720p PTZ Camera Card** (or use Manual Card):

```yaml
type: custom:mijia-ptz-card
title: Wohnzimmer Kamera
camera_entity: camera.mijia_720p
camera_ip: 192.168.1.120
show_presets: true
show_controls: true
```

*Note: You can also configure all card settings directly through the visual card editor!*

---

## 🛠️ Automations & Services

The integration provides the following services for use in Home Assistant automations and scripts:

* `mijia_720p.ptz_move`:
  ```yaml
  service: mijia_720p.ptz_move
  data:
    direction: left # up, down, left, right
    step: 3
  ```
* `mijia_720p.ptz_goto`:
  ```yaml
  service: mijia_720p.ptz_goto
  data:
    x: 16 # Pan: 0..31
    y: 7  # Tilt: 0..15
  ```
* `mijia_720p.ptz_center`: Center camera at (16, 7).
* `mijia_720p.ptz_preset`:
  ```yaml
  service: mijia_720p.ptz_preset
  data:
    id: 1 # Preset 1..4
  ```
