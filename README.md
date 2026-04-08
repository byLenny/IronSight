# IronSight (Standalone USB-to-IP Camera Server)

IronSight is a highly optimized, hardware-accelerated standalone bridge that turns any standard attached USB Camera into an Enterprise-grade IP Camera serving multiplexed RTSP/RTMP feeds.


It ships with a completely native Python Engine backed by OpenCV and FFmpeg, alongside a beautiful React-based Web Dashboard to tune live brightness, contrast, and software enhancements (CLAHE) with zero camera downtime.

## 🚀 How to Run & Deploy (Docker / Production)

The fastest and safest way to deploy the system in production is via Docker. This ensures isolation and automatically fulfills FFmpeg and OpenCV dependencies.

1. Clone or unpack the repository.
2. If using Linux/Windows with Docker, simply run:
   ```bash
   # Windows PowerShell
   ./start_docker.ps1

   # Linux/macOS
   ./start_docker.sh
   ```
   *(Alternatively: `docker compose up --build -d`)*

3. **Access the Web Panel**: Navigate to `http://localhost:8000`
4. **Login**: The default administration password is `secretpassword` (you can configure this in the `docker-compose.yml`!).

### Exposing USB Cameras via Docker
In `docker-compose.yml`, the container runs with `privileged: true` to auto-discover all `/dev/video*` hardware. If you prefer strict privileges, you can disable privileged mode and explicitly map them:
```yaml
devices:
  - "/dev/video0:/dev/video0"
  - "/dev/video1:/dev/video1"
```

## 💻 How to Run (Natively)

If you do not want to use Docker, you can run the server directly on your host machine.

### Requirements
- **Python 3.11+**
- **FFmpeg** (Must be installed and added to your system `PATH`)

### Startup
Open a terminal in the root directory and run the initialization wrapper:
```bash
# Windows PowerShell
./start_native.ps1

# Linux / bash environments
./start_native.sh
```
*(These scripts automatically install pip dependencies and start the asynchronous Uvicorn server serving both the backend endpoints and the compiled React dashboard).*

### ❄️ NixOS Users
If you run NixOS, the repository ships with a fully reproducible `flake.nix`.
```bash
nix develop
./start_native.sh
```
The python bootloader detects Nix environments automatically and natively executes the `mediamtx` binary packaged in your environment rather than downloading unsupported binaries over the internet.

## 🛠 How to Develop & Contribute

The system is split into two asynchronous environments. For frontend live-reloading, you want to run the API and Web UI separately.

### 1. Boot up the Backend (FastAPI)
Run the Python engine natively. This handles hardware access, ffmpeg pipes, and MediaMTX.
```bash
export ADMIN_PASSWORD="my_dev_password"
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Boot up the Frontend (Vite + React)
Open a second terminal to manage the Web UI:
```bash
cd frontend
npm install
npm run dev
```

Vite will start a hot-reloading dev server at `http://localhost:5173`. Any changes to `Dashboard.jsx`, the components, or `index.css` will reflect instantly. The frontend is hard-coded during development to tunnel all authenticated API requests to `http://localhost:8000` via CORS!

## 📡 Accessing Streams
Once configured through the Web Panel, your hardware is intelligently ported as RTSP networks. By default, MediaMTX serves out of port `8554`. 

If you rename a camera ID in the panel to `garage`, you can load it in VLC or Frigate/BlueIris at:
- **Raw Stream**: `rtsp://localhost:8554/garage_raw`
- **Enhanced Stream**: `rtsp://localhost:8554/garage_enh`
