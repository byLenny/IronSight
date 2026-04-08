import logging
import subprocess
import threading
import time

_LOGGER = logging.getLogger(__name__)

class StreamEncoder:
    """Encodes a single continuous stream of frames to a local RTSP URL."""
    def __init__(self, index, stream_name, width, height, fps, get_frame_func, rtsp_url):
        self.index = index
        self._name = stream_name
        self._width = width
        self._height = height
        self._fps = fps
        self._get_frame = get_frame_func
        self._rtsp_url = rtsp_url
        self._process = None
        self._stop_event = threading.Event()
        self._thread = None
        
    def start(self):
        self._stop_event.clear()
        
        # Native ffmpeg push to RTSP
        
        command = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{self._width}x{self._height}",
            "-pix_fmt", "bgr24",
            "-r", str(self._fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-f", "rtsp",
            "-rtsp_transport", "tcp",
            self._rtsp_url
        ]

        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        _LOGGER.debug(f"Started ffmpeg push encoder for {self._rtsp_url}")

    def _run_loop(self):
        """Continuously grab frames and pipe them into ffmpeg stdin."""
        target_delay = 1.0 / self._fps
        while not self._stop_event.is_set():
            start_time = time.time()
            frame = self._get_frame()
            if frame is not None and self._process and self._process.poll() is None:
                try:
                    self._process.stdin.write(frame.tobytes())
                except (BrokenPipeError, OSError):
                    _LOGGER.error(f"ffmpeg pipe broken for {self._name}")
                    break
            
            elapsed = time.time() - start_time
            if elapsed < target_delay:
                time.sleep(target_delay - elapsed)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None

class FFmpegEncoder:
    def __init__(self, video_manager):
        self.video_manager = video_manager
        self.index = video_manager.index
        
        # We push to our default MediaMTX instance on 8554
        cam_id = video_manager.camera_id
        
        self.raw_rtsp_url = f"rtsp://127.0.0.1:8554/{cam_id}_raw"
        self.enh_rtsp_url = f"rtsp://127.0.0.1:8554/{cam_id}_enh"

        self._raw_encoder = StreamEncoder(
            self.index, "raw", 
            video_manager.width, video_manager.height, video_manager.fps,
            video_manager.get_raw_bgr_frame, self.raw_rtsp_url
        )
        self._enh_encoder = StreamEncoder(
            self.index, "enhanced", 
            video_manager.width, video_manager.height, video_manager.fps,
            video_manager.get_enhanced_bgr_frame, self.enh_rtsp_url
        )

    def start(self):
        self._raw_encoder.start()
        self._enh_encoder.start()

    def stop(self):
        self._raw_encoder.stop()
        self._enh_encoder.stop()
