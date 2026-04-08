"""RTSP Server Manager for launching mediamtx."""
import logging
import os
import platform
import subprocess
import threading
import tempfile
import urllib.request
import tarfile
import zipfile
import shutil

_LOGGER = logging.getLogger(__name__)

# mediamtx release version
VERSION = "1.5.0"
RTSP_PORT = 8554
RTMP_PORT = 1935

class RTSPManager:
    def __init__(self):
        self.process = None
        self.exe_path = ""
        self.working_dir = ""

    def _get_download_url(self):
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Translate architectures
        arch = ""
        if "x86_64" in machine or "amd64" in machine:
            arch = "amd64"
        elif "arm" in machine or "aarch64" in machine:
             arch = "arm64" if "64" in machine else "armv7"

        if system == "linux":
            return f"https://github.com/bluenviron/mediamtx/releases/download/v{VERSION}/mediamtx_v{VERSION}_linux_{arch}.tar.gz"
        elif system == "windows":
             return f"https://github.com/bluenviron/mediamtx/releases/download/v{VERSION}/mediamtx_v{VERSION}_windows_{arch}.zip"
        elif system == "darwin":
             return f"https://github.com/bluenviron/mediamtx/releases/download/v{VERSION}/mediamtx_v{VERSION}_darwin_{arch}.tar.gz"
        
        raise RuntimeError(f"Unsupported OS/Arch combo: {system}/{machine}")

    def setup_and_start(self):
        """Find or download the MTX server and start it."""
        self.working_dir = os.path.join(os.path.dirname(__file__), "mediamtx_bin")
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        system_mtx = shutil.which("mediamtx")
        if system_mtx:
            self.exe_path = system_mtx
            _LOGGER.info(f"Using system-provided MediaMTX found at {self.exe_path}")
        else:
            is_windows = platform.system().lower() == "windows"
            self.exe_path = os.path.join(self.working_dir, "mediamtx.exe" if is_windows else "mediamtx")
    
            if not os.path.exists(self.exe_path):
                _LOGGER.info("Downloading MediaMTX for RTSP/RTMP support...")
                url = self._get_download_url()
                download_path = os.path.join(self.working_dir, "downloaded_mtx")
                urllib.request.urlretrieve(url, download_path)
            
            if url.endswith(".zip"):
                with zipfile.ZipFile(download_path, 'r') as z:
                    z.extractall(self.working_dir)
            else:
                with tarfile.open(download_path, "r:gz") as t:
                    t.extractall(self.working_dir)
                    
            if not is_windows:
                os.chmod(self.exe_path, 0o755)

        # Create basic mediamtx.yml in working dir
        config = f"""
rtspAddress: :{RTSP_PORT}
rtmpAddress: :{RTMP_PORT}
hls: no
webrtc: no
rtmp: yes
        """
        config_path = os.path.join(self.working_dir, "mediamtx.yml")
        with open(config_path, "w") as f:
            f.write(config)

        # Launch process
        _LOGGER.debug("Starting MediaMTX server")
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        self.process = subprocess.Popen(
            [self.exe_path, config_path],
            cwd=self.working_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo
        )

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
