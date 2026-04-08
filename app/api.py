import asyncio
import json
import os
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .auth import verify_token
# Note: we manage instances dynamically in main.py, but API needs to access them
# We will inject a registry or use a global. For simplicity, global state here:

class CameraState:
    def __init__(self):
        self.managers = {} # index -> VideoManager
        self.encoders = {} # index -> FFmpegEncoder
        self.config_file = "/app/data/config.json"
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self, index: int, options: dict):
        cfg = self.load_config()
        if str(index) not in cfg:
            cfg[str(index)] = {}
        cfg[str(index)].update(options)
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(cfg, f)

state = CameraState()

api_router = APIRouter()

class UpdateOptions(BaseModel):
    camera_id: str | None = None
    width: int | None = None
    height: int | None = None
    fps: int | None = None
    enhance_sharpen: bool | None = None
    enhance_clahe: bool | None = None
    enhance_brightness: float | None = None
    enhance_contrast: float | None = None
    hardware_props: Dict[str, Any] | None = None

def get_manager_and_enc_by_id(camera_id: str):
    for idx, mgr in state.managers.items():
        if mgr.camera_id == camera_id:
            return mgr, state.encoders.get(idx)
    return None, None

@api_router.get("/cameras")
def get_cameras(authorized: bool = Depends(verify_token)):
    res = []
    for idx, mgr in state.managers.items():
        is_running = mgr.is_running
        res.append({
            "camera_id": mgr.camera_id,
            "index": idx,
            "running": is_running,
            "options": mgr._options,
            "rtsp_raw": f"rtsp://localhost:8554/{mgr.camera_id}_raw",
            "rtsp_enh": f"rtsp://localhost:8554/{mgr.camera_id}_enh",
            "available_hardware_props": list(mgr.query_available_props().keys()),
            "current_hardware_props": mgr.get_current_props_values() if is_running else {}
        })
    return res

@api_router.patch("/cameras/{camera_id}")
def update_camera(camera_id: str, opts: UpdateOptions, authorized: bool = Depends(verify_token)):
    mgr, enc = get_manager_and_enc_by_id(camera_id)
    if not mgr:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    update_dict = {k:v for k,v in opts.model_dump().items() if v is not None and k != "hardware_props"}
    
    # Handle camera_id change specifically
    if opts.camera_id and opts.camera_id != mgr.camera_id:
        if get_manager_and_enc_by_id(opts.camera_id)[0] is not None:
            raise HTTPException(status_code=400, detail="Camera ID already exists")
            
        was_running = mgr.is_running
        if enc:
            enc.stop()
        mgr.camera_id = opts.camera_id
        update_dict["camera_id"] = opts.camera_id
        
        # Reset encoder completely with new URL
        from .core.ffmpeg_encoder import FFmpegEncoder
        new_enc = FFmpegEncoder(mgr)
        state.encoders[mgr.index] = new_enc
        if was_running:
            new_enc.start()

    mgr.update_options(update_dict)
    state.save_config(mgr.index, update_dict)
    
    if opts.hardware_props:
        props_map = mgr.query_available_props()
        for k, v in opts.hardware_props.items():
            if k in props_map:
                mgr.set_hardware_prop(props_map[k], float(v))
                
    return {"status": "ok"}

@api_router.post("/cameras/{camera_id}/start")
def start_camera(camera_id: str, authorized: bool = Depends(verify_token)):
    mgr, enc = get_manager_and_enc_by_id(camera_id)
    if not mgr:
         raise HTTPException(status_code=404, detail="Camera not found")
    if not mgr.is_running:
         mgr.start()
         if enc: enc.start()
    return {"status": "started"}

@api_router.post("/cameras/{camera_id}/stop")
def stop_camera(camera_id: str, authorized: bool = Depends(verify_token)):
    mgr, enc = get_manager_and_enc_by_id(camera_id)
    if not mgr:
         raise HTTPException(status_code=404, detail="Camera not found")
    if mgr.is_running:
         if enc: enc.stop()
         mgr.stop()
    return {"status": "stopped"}

@api_router.get("/cameras/{camera_id}/preview")
async def camera_preview(camera_id: str, token: str):
    # Preview stream is long-lived, we might validate token first
    try:
        verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    mgr, _ = get_manager_and_enc_by_id(camera_id)
    if not mgr:
         raise HTTPException(status_code=404, detail="Camera not found")
    
    async def generate():
        while mgr.is_running:
            jpeg = mgr.get_enhanced_jpeg()
            if jpeg:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')
            await asyncio.sleep(0.1) # ~10fps preview
            
    if not mgr.is_running:
         raise HTTPException(status_code=400, detail="Camera is not running")

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")
