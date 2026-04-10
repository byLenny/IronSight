import { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { Camera, LogOut, Settings2, Play, Square, LayoutGrid, MonitorPlay } from 'lucide-react';
import { AuthContext } from './Auth';

function CameraControl({ camera, onRefresh }) {
  const { token } = useContext(AuthContext);
  const [opts, setOpts] = useState(camera.options);
  const [hardwareProps, setHardwareProps] = useState(camera.current_hardware_props || {});

  const handleUpdate = async (field, value, isHardware = false) => {
    const newOpts = { ...opts };
    const newHardware = { ...hardwareProps };

    if (isHardware) {
      newHardware[field] = parseFloat(value);
      setHardwareProps(newHardware);
    } else {
      newOpts[field] = value;
      setOpts(newOpts);
    }

    try {
      const payload = isHardware ? { hardware_props: { [field]: value } } : { [field]: value };
      await axios.patch(`/api/cameras/${camera.camera_id}`, payload);
    } catch (err) {
      console.error(err);
    }
  };

  const handleUpdateId = async (newId) => {
    try {
      await axios.patch(`/api/cameras/${camera.camera_id}`, { camera_id: newId });
      onRefresh();
    } catch (err) {
      alert("Failed to update ID (might already exist or be invalid)");
    }
  };

  const handleToggleState = async () => {
    try {
      if (camera.running) await axios.post(`/api/cameras/${camera.camera_id}/stop`);
      else await axios.post(`/api/cameras/${camera.camera_id}/start`);
      onRefresh();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="glass-panel camera-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <MonitorPlay size={24} color="var(--accent-color)" /> {camera.camera_id}
        </h2>
        <span className={`status-badge ${camera.running ? 'active' : 'inactive'}`}>
          <div style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: camera.running ? '#34d399' : '#f87171' }} />
          {camera.running ? 'Live' : 'Stopped'}
        </span>
      </div>

      <div className="setting-item" style={{ marginBottom: '-0.5rem' }}>
        <input type="text"
          defaultValue={camera.camera_id}
          onBlur={(e) => { if (e.target.value !== camera.camera_id && e.target.value.length > 0) handleUpdateId(e.target.value) }}
          placeholder="Camera Identifier (Alias)" />
      </div>

      <div className="preview-container">
        {camera.running ? (
          <img
            src={`http://localhost:8008/api/cameras/${camera.camera_id}/preview?token=${token}&ts=${Date.now()}`}
            alt={`${camera.camera_id} Preview`}
            // Add error handling to fall back
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }}
          />
        ) : null}
        <div className="preview-placeholder" style={{ display: camera.running ? 'none' : 'block' }}>
          {camera.running ? 'Loading preview...' : 'Camera is stopped.'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) auto', gap: '1rem' }}>
        <button className={camera.running ? "danger" : "success"} onClick={handleToggleState}>
          {camera.running ? <><Square size={18} /> Stop Stream</> : <><Play size={18} /> Start Stream</>}
        </button>
      </div>

      <div className="streams-list">
        <p><strong>Raw Stream:</strong> <code>{camera.rtsp_raw}</code></p>
        <p><strong>Enhanced Stream:</strong> <code>{camera.rtsp_enh}</code></p>
        {/* They map directly to RTSP Manager at MediaMTX as well: rtsp://localhost:8554/stream */}
      </div>

      <div className="settings-group">
        <h3 style={{ fontSize: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Software Enhancements</h3>

        <div className="setting-item">
          <label className="toggle-switch">
            <input type="checkbox" checked={opts.enhance_sharpen || false} onChange={(e) => handleUpdate('enhance_sharpen', e.target.checked)} />
            <span className="toggle-slider"></span>
            <span className="setting-label">Enable Sharpening</span>
          </label>
        </div>

        <div className="setting-item">
          <label className="toggle-switch">
            <input type="checkbox" checked={opts.enhance_clahe || false} onChange={(e) => handleUpdate('enhance_clahe', e.target.checked)} />
            <span className="toggle-slider"></span>
            <span className="setting-label">Enable Auto-Contrast (CLAHE)</span>
          </label>
        </div>

        <div className="setting-item">
          <div className="setting-label"><span>Software Contrast</span> <span>{opts.enhance_contrast || 1.0}</span></div>
          <input type="range" min="0.5" max="3" step="0.1" value={opts.enhance_contrast || 1.0} onChange={(e) => handleUpdate('enhance_contrast', parseFloat(e.target.value))} />
        </div>

        <div className="setting-item">
          <div className="setting-label"><span>Software Brightness</span> <span>{opts.enhance_brightness || 0}</span></div>
          <input type="range" min="-100" max="100" step="1" value={opts.enhance_brightness || 0} onChange={(e) => handleUpdate('enhance_brightness', parseInt(e.target.value))} />
        </div>

        {camera.available_hardware_props?.length > 0 && (
          <>
            <h3 style={{ fontSize: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', marginTop: '1rem' }}>Hardware Properties</h3>
            {camera.available_hardware_props.map(prop => (
              <div className="setting-item" key={prop}>
                <div className="setting-label"><span>{prop}</span> <span>{hardwareProps[prop] ?? 0}</span></div>
                <input type="range" min={prop === 'Brightness' ? -255 : 0} max="255" step="1"
                  value={hardwareProps[prop] ?? 0}
                  onChange={(e) => handleUpdate(prop, e.target.value, true)} />
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

function Dashboard() {
  const [cameras, setCameras] = useState([]);
  const { logout } = useContext(AuthContext);

  const fetchCameras = async () => {
    try {
      const res = await axios.get('/api/cameras');
      setCameras(res.data);
    } catch (err) {
      if (err.response?.status === 401) logout();
    }
  };

  useEffect(() => {
    fetchCameras();
    const inv = setInterval(fetchCameras, 5000);
    return () => clearInterval(inv);
  }, []);

  return (
    <>
      <header className="glass-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <LayoutGrid size={28} color="var(--accent-color)" />
          <h1 style={{ margin: 0 }}>IronSight</h1>
        </div>
        <button className="secondary" onClick={logout} style={{ padding: '0.5rem 1rem' }}>
          <LogOut size={16} /> Sign out
        </button>
      </header>

      <main className="dashboard-container">
        {cameras.length === 0 ? (
          <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <Camera size={48} color="var(--text-secondary)" style={{ opacity: 0.5, margin: '0 auto 1rem' }} />
            <h2 style={{ color: 'var(--text-secondary)' }}>No USB Cameras Found</h2>
            <p style={{ color: 'var(--text-secondary)' }}>Ensure they are plugged in and Docker has `privileged: true` set.</p>
          </div>
        ) : (
          <div className="cameras-grid">
            {cameras.map(c => <CameraControl key={c.camera_id} camera={c} onRefresh={fetchCameras} />)}
          </div>
        )}
      </main>
    </>
  );
}

export default Dashboard;
