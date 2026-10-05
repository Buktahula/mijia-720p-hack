/**
 * Mijia 720p Hack - Web Client Controller
 * Pure vanilla JavaScript - no external libraries
 */

const App = {
  step: 3, // Default step size (Normal)
  apiBase: 'api',
  useCgi: false,
  pollTimer: null,
  isMoving: false,

  init() {
    this.detectApi();
    this.setupEventListeners();
    this.refreshAll();
    this.startPolling();
  },

  // Auto detect if PHP is running, otherwise fallback to CGI
  async detectApi() {
    try {
      const res = await fetch(`${this.apiBase}/motor.php?action=status`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      if (data && data.status === 'ok') {
        this.useCgi = false;
        return;
      }
    } catch (e) {
      // Fallback to CGI
      this.useCgi = true;
      console.warn('PHP API not responding, falling back to CGI');
    }
  },

  getEndpoint(name) {
    if (this.useCgi) {
      return `${this.apiBase}/${name}.cgi`;
    }
    return `${this.apiBase}/${name}.php`;
  },

  async request(endpoint, params = {}) {
    const url = new URL(this.getEndpoint(endpoint), window.location.origin);
    const options = {
      headers: { 'Accept': 'application/json' }
    };

    if (params.method === 'POST') {
      options.method = 'POST';
      options.headers['Content-Type'] = 'application/json';
      delete params.method;
      options.body = JSON.stringify(params);
    } else {
      Object.keys(params).forEach(k => {
        if (params[k] !== undefined && params[k] !== null) {
          url.searchParams.append(k, params[k]);
        }
      });
    }

    try {
      const res = await fetch(url.toString(), options);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      return await res.json();
    } catch (err) {
      console.error('Request failed:', err);
      this.showToast(err.message, 'error');
      throw err;
    }
  },

  showToast(msg, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'error' : ''}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },

  // Motor / PTZ Controls
  async move(dir) {
    if (this.isMoving) return;
    this.isMoving = true;
    try {
      const data = await this.request('motor', {
        action: 'move',
        dir: dir,
        step: this.step
      });
      if (data && data.motor) {
        this.updateMotorUI(data.motor);
      }
    } finally {
      this.isMoving = false;
    }
  },

  async center() {
    this.showToast('Centering camera...');
    const data = await this.request('motor', { action: 'center' });
    if (data && data.motor) this.updateMotorUI(data.motor);
  },

  async calibrate() {
    if (!confirm('Calibrate camera motors? The camera will sweep end-to-end to find limits.')) return;
    this.showToast('Calibrating motors, please wait...');
    const data = await this.request('motor', { action: 'calibrate' });
    if (data && data.motor) {
      this.updateMotorUI(data.motor);
      this.showToast('Calibration complete!');
    }
  },

  async gotoPreset(id) {
    this.showToast(`Moving to Preset ${id}...`);
    const data = await this.request('motor', { action: 'preset', id: id });
    if (data && data.motor) {
      this.updateMotorUI(data.motor);
    }
  },

  async savePreset(id) {
    const data = await this.request('motor', { action: 'set_preset', id: id });
    this.showToast(`Preset ${id} saved!`);
    if (data && data.presets) {
      this.updatePresetsUI(data.presets);
    }
  },

  async setGoto(x, y) {
    const data = await this.request('motor', { action: 'goto', x: x, y: y });
    if (data && data.motor) this.updateMotorUI(data.motor);
  },

  updateMotorUI(motor) {
    if (!motor) return;
    const h = motor.horizontal;
    const v = motor.vertical;
    if (h && h.x !== undefined) {
      const elX = document.getElementById('ptz-x-val');
      if (elX) elX.textContent = h.x;
      const barX = document.getElementById('ptz-x-bar');
      if (barX) barX.style.width = `${(h.x / 31) * 100}%`;
    }
    if (v && v.y !== undefined) {
      const elY = document.getElementById('ptz-y-val');
      if (elY) elY.textContent = v.y;
      const barY = document.getElementById('ptz-y-bar');
      if (barY) barY.style.width = `${(v.y / 15) * 100}%`;
    }
  },

  updatePresetsUI(presets) {
    if (!presets) return;
    for (let i = 1; i <= 4; i++) {
      const p = presets[`preset_${i}`];
      if (p) {
        const el = document.getElementById(`preset-coords-${i}`);
        if (el) el.textContent = `(${p.x}, ${p.y})`;
      }
    }
  },

  // Camera Hardware Controls
  async setNightMode(mode) {
    const data = await this.request('camera', { action: 'night_mode', mode: mode });
    if (data && data.camera) this.updateCameraUI(data.camera);
    this.showToast(`Night mode: ${mode}`);
  },

  async setIrCut(state) {
    const data = await this.request('camera', { action: 'ir_cut', state: state ? 'on' : 'off' });
    if (data && data.camera) this.updateCameraUI(data.camera);
    this.showToast(`IR-Cut filter: ${state ? 'On' : 'Off'}`);
  },

  async setIrLed(val) {
    const data = await this.request('camera', { action: 'ir_led', value: val });
    if (data && data.camera) this.updateCameraUI(data.camera);
  },

  async setFlip(state) {
    const data = await this.request('camera', { action: 'flip', state: state ? 'on' : 'off' });
    if (data && data.camera) this.updateCameraUI(data.camera);
    this.showToast(`Flip image: ${state ? 'On' : 'Off'}`);
  },

  async setMirror(state) {
    const data = await this.request('camera', { action: 'mirror', state: state ? 'on' : 'off' });
    if (data && data.camera) this.updateCameraUI(data.camera);
    this.showToast(`Mirror image: ${state ? 'On' : 'Off'}`);
  },

  async setLed(color, state) {
    const data = await this.request('camera', { action: 'led', color: color, state: state });
    if (data && data.camera) this.updateCameraUI(data.camera);
    this.showToast(`${color.toUpperCase()} LED: ${state}`);
  },

  updateCameraUI(cam) {
    if (!cam) return;
    // Night mode
    const nmSelect = document.getElementById('night-mode-select');
    if (nmSelect) {
      if (cam.auto_night === 'on' || cam.night_mode_nvram === '0') {
        nmSelect.value = 'auto';
      } else if (cam.night_mode === '1' || cam.night_mode_nvram === '2') {
        nmSelect.value = 'on';
      } else {
        nmSelect.value = 'off';
      }
    }

    // IR Cut
    const irCutSw = document.getElementById('ircut-switch');
    if (irCutSw && cam.ir_cut !== null) {
      irCutSw.checked = (cam.ir_cut === '1' || cam.ir_cut === 1);
    }

    // IR LED
    const irSlider = document.getElementById('irled-slider');
    const irVal = document.getElementById('irled-val');
    if (irSlider && cam.ir_led !== undefined) {
      irSlider.value = cam.ir_led;
      if (irVal) irVal.textContent = cam.ir_led;
    }

    // Flip & Mirror
    const flipSw = document.getElementById('flip-switch');
    if (flipSw && cam.flip !== null) flipSw.checked = (cam.flip === '1' || cam.flip === 1);

    const mirrorSw = document.getElementById('mirror-switch');
    if (mirrorSw && cam.mirror !== null) mirrorSw.checked = (cam.mirror === '1' || cam.mirror === 1);

    // LEDs
    const blueSw = document.getElementById('blue-led-switch');
    if (blueSw) blueSw.checked = (cam.blue_led === 'on');

    const yellowSw = document.getElementById('yellow-led-switch');
    if (yellowSw) yellowSw.checked = (cam.yellow_led === 'on');
  },

  // System & Service Controls
  async reboot() {
    if (!confirm('Are you sure you want to reboot the camera?')) return;
    this.showToast('Rebooting camera...');
    await this.request('system', { action: 'reboot' });
    setTimeout(() => {
      alert('Camera is rebooting. This page will reload in 30 seconds.');
      setTimeout(() => location.reload(), 30000);
    }, 1000);
  },

  async controlService(name, cmd) {
    this.showToast(`${cmd.toUpperCase()}ing ${name}...`);
    const data = await this.request('system', { action: 'service', name: name, cmd: cmd });
    if (data && data.system) this.updateSystemUI(data.system);
    this.showToast(`Service ${name}: ${cmd} complete`);
  },

  updateSystemUI(sys) {
    if (!sys) return;
    // Memory
    if (sys.memory && sys.memory.total_kb > 0) {
      const pct = Math.round((sys.memory.used_kb / sys.memory.total_kb) * 100);
      const el = document.getElementById('sys-mem-text');
      const bar = document.getElementById('sys-mem-bar');
      if (el) el.textContent = `${Math.round(sys.memory.used_kb / 1024)}MB / ${Math.round(sys.memory.total_kb / 1024)}MB (${pct}%)`;
      if (bar) {
        bar.style.width = `${pct}%`;
        bar.className = 'stat-bar-fill' + (pct > 85 ? ' danger' : (pct > 70 ? ' warning' : ''));
      }
    }

    // SD Card
    if (sys.sdcard && sys.sdcard.total_kb > 0) {
      const pct = Math.round((sys.sdcard.used_kb / sys.sdcard.total_kb) * 100);
      const el = document.getElementById('sys-sd-text');
      const bar = document.getElementById('sys-sd-bar');
      if (el) el.textContent = `${Math.round(sys.sdcard.free_kb / 1024)}MB Free / ${Math.round(sys.sdcard.total_kb / 1024)}MB`;
      if (bar) bar.style.width = `${pct}%`;
    }

    // Uptime & Load
    const elUptime = document.getElementById('sys-uptime');
    if (elUptime && sys.uptime) elUptime.textContent = sys.uptime.split(',')[0].replace('up', '').trim();

    const elLoad = document.getElementById('sys-load');
    if (elLoad && sys.loadavg) elLoad.textContent = sys.loadavg;

    // WiFi & Network
    if (sys.network) {
      const ip = sys.network.ip || window.location.hostname;
      const elIp = document.getElementById('sys-ip');
      if (elIp) elIp.textContent = ip;
      
      const elRtsp = document.getElementById('rtsp-url');
      if (elRtsp) elRtsp.textContent = `rtsp://${ip}:554/live/ch00_0`;

      const elSsid = document.getElementById('sys-wifi-ssid');
      if (elSsid) elSsid.textContent = sys.network.ssid || 'Unknown';

      const elSig = document.getElementById('sys-wifi-signal');
      if (elSig) elSig.textContent = sys.network.signal ? `${sys.network.signal}%` : 'N/A';
    }

    // Services Badges
    if (sys.services) {
      Object.keys(sys.services).forEach(s => {
        const badge = document.getElementById(`srv-badge-${s}`);
        if (badge) {
          const st = sys.services[s];
          badge.textContent = st;
          badge.className = `badge ${st === 'running' || st === 'disabled' ? 'badge-success' : 'badge-neutral'}`;
        }
      });
    }
  },

  async refreshAll() {
    try {
      const [motorRes, camRes, sysRes] = await Promise.all([
        this.request('motor', { action: 'status' }).catch(() => null),
        this.request('camera', { action: 'status' }).catch(() => null),
        this.request('system', { action: 'info' }).catch(() => null)
      ]);
      if (motorRes && motorRes.motor) this.updateMotorUI(motorRes.motor);
      if (motorRes && motorRes.presets) this.updatePresetsUI(motorRes.presets);
      if (camRes && camRes.camera) this.updateCameraUI(camRes.camera);
      if (sysRes && sysRes.system) this.updateSystemUI(sysRes.system);
    } catch (e) {
      console.warn('Initial refresh incomplete', e);
    }
  },

  startPolling() {
    this.pollTimer = setInterval(() => {
      // Periodic stats update
      this.request('system', { action: 'info' })
        .then(res => { if (res && res.system) this.updateSystemUI(res.system); })
        .catch(() => {});
    }, 10000);
  },

  setupEventListeners() {
    // Keyboard arrow keys for PTZ navigation
    window.addEventListener('keydown', (e) => {
      // Don't trigger if typing in an input
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
      
      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          this.move('up');
          break;
        case 'ArrowDown':
          e.preventDefault();
          this.move('down');
          break;
        case 'ArrowLeft':
          e.preventDefault();
          this.move('left');
          break;
        case 'ArrowRight':
          e.preventDefault();
          this.move('right');
          break;
        case 'Home':
          e.preventDefault();
          this.center();
          break;
      }
    });

    // Step selector buttons
    document.querySelectorAll('.step-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.step-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.step = parseInt(btn.dataset.step) || 3;
      });
    });
  },

  copyRtspUrl() {
    const url = document.getElementById('rtsp-url')?.textContent;
    if (url) {
      navigator.clipboard.writeText(url).then(() => {
        this.showToast('RTSP URL copied to clipboard!');
      });
    }
  },

  copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
      this.showToast('Copied to clipboard!');
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
