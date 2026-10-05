/**
 * Mijia 720p PTZ Camera Card for Home Assistant Lovelace
 * Author: Antigravity / Jan Sperling / Community
 * Zero YAML needed - Full GUI config support & tactile D-Pad controls
 */

class MijiaPtzCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._step = 3;
    this._pan = 16;
    this._tilt = 7;
    this._isMoving = false;
  }

  static getStubConfig() {
    return {
      title: "Mijia 720p PTZ",
      camera_entity: "camera.mijia_720p",
      camera_ip: "",
      show_presets: true,
      show_controls: true,
      step_size: 3
    };
  }

  static async getConfigElement() {
    return document.createElement("mijia-ptz-card-editor");
  }

  setConfig(config) {
    if (!config.camera_entity && !config.camera_ip) {
      throw new Error("Please specify either camera_entity or camera_ip");
    }
    this._config = Object.assign({
      title: "Mijia 720p Camera",
      show_presets: true,
      show_controls: true,
      step_size: 3
    }, config);
    this._step = this._config.step_size;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.updateCardState();
  }

  async sendCommand(action, params = {}) {
    if (this._isMoving) return;
    this._isMoving = true;

    try {
      // Method 1: Direct IP call if camera_ip is provided
      if (this._config.camera_ip) {
        const url = new URL(`http://${this._config.camera_ip}/api/motor.php`);
        url.searchParams.append('action', action);
        Object.keys(params).forEach(k => url.searchParams.append(k, params[k]));
        const res = await fetch(url.toString());
        const data = await res.json();
        if (data && data.motor) {
          this.updateCoords(data.motor.horizontal?.x, data.motor.vertical?.y);
        }
        return;
      }

      // Method 2: Via Home Assistant Service / Entities
      if (this._hass) {
        if (action === 'move') {
          const dir = params.dir;
          const entityId = `button.mijia_720p_ptz_${dir}`;
          if (this._hass.states[entityId]) {
            await this._hass.callService('button', 'press', { entity_id: entityId });
          } else {
            await this._hass.callService('mijia_720p', 'ptz_move', {
              direction: dir,
              step: this._step
            });
          }
        } else if (action === 'center') {
          const entityId = `button.mijia_720p_ptz_center`;
          if (this._hass.states[entityId]) {
            await this._hass.callService('button', 'press', { entity_id: entityId });
          } else {
            await this._hass.callService('mijia_720p', 'ptz_center', {});
          }
        } else if (action === 'preset') {
          const entityId = `button.mijia_720p_preset_${params.id}`;
          if (this._hass.states[entityId]) {
            await this._hass.callService('button', 'press', { entity_id: entityId });
          } else {
            await this._hass.callService('mijia_720p', 'ptz_preset', { id: params.id });
          }
        } else if (action === 'calibrate') {
          const entityId = `button.mijia_720p_ptz_calibrate`;
          if (this._hass.states[entityId]) {
            await this._hass.callService('button', 'press', { entity_id: entityId });
          }
        }
      }
    } catch (e) {
      console.error("PTZ Command failed:", e);
    } finally {
      setTimeout(() => { this._isMoving = false; }, 400);
    }
  }

  updateCoords(x, y) {
    if (x !== undefined) this._pan = x;
    if (y !== undefined) this._tilt = y;
    const elPan = this.shadowRoot.getElementById('pan-val');
    const elTilt = this.shadowRoot.getElementById('tilt-val');
    if (elPan) elPan.textContent = this._pan;
    if (elTilt) elTilt.textContent = this._tilt;
  }

  updateCardState() {
    if (!this._hass || !this.shadowRoot) return;

    // Read Pan / Tilt sensors if present
    const panState = this._hass.states['sensor.mijia_720p_pan_position'];
    const tiltState = this._hass.states['sensor.mijia_720p_tilt_position'];
    if (panState && panState.state !== 'unavailable') this._pan = panState.state;
    if (tiltState && tiltState.state !== 'unavailable') this._tilt = tiltState.state;
    this.updateCoords(this._pan, this._tilt);

    // Update camera stream / poster
    if (this._config.camera_entity) {
      const camState = this._hass.states[this._config.camera_entity];
      const img = this.shadowRoot.getElementById('camera-img');
      if (img && camState && camState.attributes && camState.attributes.entity_picture) {
        img.src = this._hass.hassUrl(camState.attributes.entity_picture);
      }
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          overflow: hidden;
          background: var(--ha-card-background, var(--card-background-color, #1c1c1c));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 4px 12px rgba(0,0,0,0.3));
          color: var(--primary-text-color, #ffffff);
          font-family: var(--paper-font-body1_-_font-family, sans-serif);
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px 16px;
          background: rgba(0,0,0,0.2);
          border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .title {
          font-size: 1.1rem;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .coord-badge {
          font-family: monospace;
          font-size: 0.8rem;
          background: rgba(0, 194, 136, 0.15);
          color: #00c288;
          border: 1px solid rgba(0, 194, 136, 0.3);
          padding: 3px 8px;
          border-radius: 999px;
        }
        .stream-container {
          position: relative;
          width: 100%;
          aspect-ratio: 16 / 9;
          background: #0a0a0a;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .stream-container img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        /* D-Pad Container */
        .controls-overlay {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 14px 16px;
          background: rgba(18, 24, 32, 0.95);
          gap: 16px;
          flex-wrap: wrap;
        }
        .dpad {
          position: relative;
          width: 140px;
          height: 140px;
          background: #111722;
          border-radius: 50%;
          border: 2px solid #283548;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .dpad-btn {
          position: absolute;
          width: 40px;
          height: 40px;
          background: #1d2737;
          border: 1px solid #283548;
          color: #fff;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          user-select: none;
          transition: all 0.15s ease;
        }
        .dpad-btn:active {
          background: #00c288;
          color: #000;
          transform: scale(0.92);
        }
        .dpad-up { top: 6px; }
        .dpad-down { bottom: 6px; }
        .dpad-left { left: 6px; }
        .dpad-right { right: 6px; }
        .dpad-center {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: #151d29;
        }
        /* Right Side: Step Size & Presets */
        .side-panel {
          flex: 1;
          min-width: 160px;
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .btn-group {
          display: flex;
          border-radius: 6px;
          overflow: hidden;
          border: 1px solid #283548;
        }
        .btn-group button {
          flex: 1;
          background: #1d2737;
          border: none;
          color: #94a3b8;
          padding: 6px 4px;
          font-size: 0.78rem;
          font-weight: 600;
          cursor: pointer;
          border-right: 1px solid #283548;
        }
        .btn-group button:last-child {
          border-right: none;
        }
        .btn-group button.active {
          background: #00c288;
          color: #000;
        }
        .presets-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 6px;
        }
        .preset-btn {
          background: #1d2737;
          border: 1px solid #283548;
          color: #e2e8f0;
          border-radius: 6px;
          padding: 6px;
          font-size: 0.8rem;
          font-weight: 500;
          cursor: pointer;
          text-align: center;
          transition: background 0.15s;
        }
        .preset-btn:hover {
          background: #2a374c;
          border-color: #00c288;
        }
        .preset-btn:active {
          background: #00c288;
          color: #000;
        }
        .action-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 4px;
        }
        .action-link {
          color: #94a3b8;
          font-size: 0.75rem;
          cursor: pointer;
          text-decoration: underline;
        }
        .action-link:hover {
          color: #00c288;
        }
      </style>

      <ha-card>
        <div class="header">
          <div class="title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#00c288"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>
            ${this._config.title}
          </div>
          <div class="coord-badge">
            Pan: <span id="pan-val">${this._pan}</span> | Tilt: <span id="tilt-val">${this._tilt}</span>
          </div>
        </div>

        <!-- Camera Stream / Snapshot -->
        <div class="stream-container">
          <img id="camera-img" src="" alt="Mijia Stream Preview" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'400\\' height=\\'225\\' viewBox=\\'0 0 400 225\\'><rect width=\\'400\\' height=\\'225\\' fill=\\'%23111\\'/><text x=\\'50%\\' y=\\'50%\\' fill=\\'%23666\\' font-family=\\'sans-serif\\' font-size=\\'14\\' text-anchor=\\'middle\\'>Connecting to Stream...</text></svg>'">
        </div>

        <!-- Controls Overlay -->
        ${this._config.show_controls ? `
          <div class="controls-overlay">
            <!-- D-Pad -->
            <div class="dpad">
              <button class="dpad-btn dpad-up" id="btn-up" title="Tilt Up">▲</button>
              <button class="dpad-btn dpad-down" id="btn-down" title="Tilt Down">▼</button>
              <button class="dpad-btn dpad-left" id="btn-left" title="Pan Left">◀</button>
              <button class="dpad-btn dpad-right" id="btn-right" title="Pan Right">▶</button>
              <button class="dpad-btn dpad-center" id="btn-center" title="Center">●</button>
            </div>

            <!-- Side Panel (Step Size & Presets) -->
            <div class="side-panel">
              <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Step Speed</div>
              <div class="btn-group">
                <button id="step-1" class="${this._step === 1 ? 'active' : ''}">1x Fine</button>
                <button id="step-3" class="${this._step === 3 ? 'active' : ''}">3x Norm</button>
                <button id="step-5" class="${this._step === 5 ? 'active' : ''}">5x Fast</button>
              </div>

              ${this._config.show_presets ? `
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-top: 4px;">Presets</div>
                <div class="presets-grid">
                  <button class="preset-btn" id="preset-1">Preset 1</button>
                  <button class="preset-btn" id="preset-2">Preset 2</button>
                  <button class="preset-btn" id="preset-3">Preset 3</button>
                  <button class="preset-btn" id="preset-4">Preset 4</button>
                </div>
              ` : ''}

              <div class="action-row">
                <span class="action-link" id="btn-calibrate">⚙️ Calibrate</span>
                ${this._config.camera_ip ? `
                  <a href="http://${this._config.camera_ip}/" target="_blank" class="action-link" style="text-decoration: none;">🌐 Web UI</a>
                ` : ''}
              </div>
            </div>
          </div>
        ` : ''}
      </ha-card>
    `;

    // Attach Event Handlers
    this.shadowRoot.getElementById('btn-up')?.addEventListener('click', () => this.sendCommand('move', { dir: 'up' }));
    this.shadowRoot.getElementById('btn-down')?.addEventListener('click', () => this.sendCommand('move', { dir: 'down' }));
    this.shadowRoot.getElementById('btn-left')?.addEventListener('click', () => this.sendCommand('move', { dir: 'left' }));
    this.shadowRoot.getElementById('btn-right')?.addEventListener('click', () => this.sendCommand('move', { dir: 'right' }));
    this.shadowRoot.getElementById('btn-center')?.addEventListener('click', () => this.sendCommand('center'));
    this.shadowRoot.getElementById('btn-calibrate')?.addEventListener('click', () => this.sendCommand('calibrate'));

    // Step buttons
    [1, 3, 5].forEach(s => {
      this.shadowRoot.getElementById(`step-${s}`)?.addEventListener('click', () => {
        this._step = s;
        [1, 3, 5].forEach(x => this.shadowRoot.getElementById(`step-${x}`)?.classList.remove('active'));
        this.shadowRoot.getElementById(`step-${s}`)?.classList.add('active');
      });
    });

    // Presets
    [1, 2, 3, 4].forEach(p => {
      this.shadowRoot.getElementById(`preset-${p}`)?.addEventListener('click', () => {
        this.sendCommand('preset', { id: p });
      });
    });

    this.updateCardState();
  }
}

// Visual GUI Editor for Home Assistant Lovelace Card Editor
class MijiaPtzCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this.render();
  }

  configChanged(newConfig) {
    const event = new CustomEvent("config-changed", {
      detail: { config: newConfig },
      bubbles: true,
      composed: true
    });
    this.dispatchEvent(event);
  }

  render() {
    this.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 14px; padding: 16px 0;">
        <div>
          <label style="display:block; font-weight:600; margin-bottom: 4px;">Card Title</label>
          <input type="text" id="edit-title" value="${this._config.title || ''}" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background: #222; color: #fff;">
        </div>
        <div>
          <label style="display:block; font-weight:600; margin-bottom: 4px;">Camera Entity (Home Assistant)</label>
          <input type="text" id="edit-camera" value="${this._config.camera_entity || 'camera.mijia_720p'}" placeholder="camera.mijia_720p" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background: #222; color: #fff;">
        </div>
        <div>
          <label style="display:block; font-weight:600; margin-bottom: 4px;">Camera IP Address (Direct API control without YAML)</label>
          <input type="text" id="edit-ip" value="${this._config.camera_ip || ''}" placeholder="e.g. 192.168.1.120" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #444; background: #222; color: #fff;">
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <input type="checkbox" id="edit-presets" ${this._config.show_presets !== false ? 'checked' : ''}>
          <label for="edit-presets">Show Position Presets (1-4)</label>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <input type="checkbox" id="edit-controls" ${this._config.show_controls !== false ? 'checked' : ''}>
          <label for="edit-controls">Show PTZ D-Pad Controls</label>
        </div>
      </div>
    `;

    const update = () => {
      this.configChanged({
        ...this._config,
        title: this.querySelector('#edit-title').value,
        camera_entity: this.querySelector('#edit-camera').value,
        camera_ip: this.querySelector('#edit-ip').value,
        show_presets: this.querySelector('#edit-presets').checked,
        show_controls: this.querySelector('#edit-controls').checked
      });
    };

    this.querySelectorAll('input').forEach(input => {
      input.addEventListener('change', update);
      input.addEventListener('keyup', update);
    });
  }
}

customElements.define('mijia-ptz-card', MijiaPtzCard);
customElements.define('mijia-ptz-card-editor', MijiaPtzCardEditor);

// Register in Home Assistant Lovelace Card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'mijia-ptz-card',
  name: 'Mijia 720p PTZ Camera Card',
  description: 'Interactive PTZ D-Pad and preset controls for hacked Xiaomi Mijia 720p Camera',
  preview: true
});

console.info(
  '%c MIJIA-PTZ-CARD %c v1.0.0 Loaded ',
  'color: white; background: #00c288; font-weight: 700;',
  'color: #00c288; background: #111722; font-weight: 700;'
);
