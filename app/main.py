import logging
import cv2
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os

from .auth import auth_router
from .api import api_router, state
from .core.video import VideoManager
from .core.ffmpeg_encoder import FFmpegEncoder
from .core.rtsp_server import RTSPManager

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

rtsp_manager = RTSPManager()
proxies = []

def scan_cameras():
    """Scan and return available camera indices."""
    available = []
    # Test up to 10 indices
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _LOGGER.info("Starting MediaMTX...")
    rtsp_manager.setup_and_start()
    
    _LOGGER.info("Scanning for USB Cameras...")
    indices = scan_cameras()
    _LOGGER.info(f"Found cameras: {indices}")
    
    configs = state.load_config()
    
    for idx in indices:
        opts = configs.get(str(idx), {
            "width": 640,
            "height": 480,
            "fps": 30,
            "enhance_sharpen": False,
            "enhance_clahe": False,
            "enhance_contrast": 1.0,
            "enhance_brightness": 0.0
        })
        
        mgr = VideoManager(idx, opts)
        enc = FFmpegEncoder(mgr)
        state.managers[idx] = mgr
        state.encoders[idx] = enc
        
        # Start immediately
        mgr.start()
        enc.start()
        
        _LOGGER.info(f"Started Camera {mgr.camera_id} - Raw: {enc.raw_rtsp_url} ; Enh: {enc.enh_rtsp_url}")
        
    yield
    
    # Shutdown
    _LOGGER.info("Shutting down...")
    rtsp_manager.stop()
    for mgr in state.managers.values():
        mgr.stop()
    for enc in state.encoders.values():
        enc.stop()

app = FastAPI(lifespan=lifespan)

# Allow CORS for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(api_router, prefix="/api")

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend/dist")
os.makedirs(frontend_dir, exist_ok=True) # Ensure it exists so FastAPI doesn't crash on boot if it wasn't built
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
