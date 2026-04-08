import logging
import threading
import time

_LOGGER = logging.getLogger(__name__)

class VideoManager:
    """Manages the background thread capturing and enhancing frames."""

    def __init__(self, camera_index: int, options: dict):
        self.index = camera_index
        self._options = options.copy()
        
        self.width = self._options.get("width", 640)
        self.height = self._options.get("height", 480)
        self.fps = self._options.get("fps", 30)
        self.camera_id = self._options.get("camera_id", f"cam_{camera_index}")
        
        # Thread sync
        self._stop_event = threading.Event()
        self._thread = None
        self._cap = None
        
        # Frame buffers
        self._latest_raw_bgr = None
        self._latest_enhanced_bgr = None
        self._lock = threading.Lock()
        
        # State
        self.is_running = False
        
        self._sharpen_kernel = None
        self._clahe = None

    def _init_enhancers(self, cv2, np):
        if self._options.get("enhance_sharpen"):
            self._sharpen_kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        else:
            self._sharpen_kernel = None

        if self._options.get("enhance_clahe"):
            self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        else:
            self._clahe = None

    def update_options(self, options: dict):
        with self._lock:
            self._options.update(options)
            self.width = self._options.get("width", self.width)
            self.height = self._options.get("height", self.height)
            self.fps = self._options.get("fps", self.fps)
            self.camera_id = self._options.get("camera_id", self.camera_id)
            
            import cv2
            import numpy as np
            self._init_enhancers(cv2, np)

            if self._cap and self._cap.isOpened():
                self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self._cap.set(cv2.CAP_PROP_FPS, self.fps)

    def start(self):
        """Start the background capture thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self.is_running = True
        return True

    def stop(self):
        """Stop the background capture thread."""
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        if self._cap:
            self._cap.release()
            self._cap = None

    def set_hardware_prop(self, prop_id, value):
        """Set a property on the cv2 VideoCapture."""
        if self._cap and self._cap.isOpened():
            return self._cap.set(prop_id, value)
        return False

    def get_hardware_prop(self, prop_id):
        """Get a property from the cv2 VideoCapture."""
        if self._cap and self._cap.isOpened():
            return self._cap.get(prop_id)
        return None

    def query_available_props(self):
        """Discover which properties this hardware camera supports."""
        import cv2
        props = {}
        if not self._cap or not self._cap.isOpened():
            return props
            
        test_props = {
            "Brightness": cv2.CAP_PROP_BRIGHTNESS,
            "Contrast": cv2.CAP_PROP_CONTRAST,
            "Saturation": cv2.CAP_PROP_SATURATION,
            "Hue": cv2.CAP_PROP_HUE,
            "Gain": cv2.CAP_PROP_GAIN,
            "Exposure": cv2.CAP_PROP_EXPOSURE,
        }
        
        for name, prop_id in test_props.items():
            val = self._cap.get(prop_id)
            if val != -1:  # -1 is typically returned for unsupported props
                # Some cameras return 0.0 for unsupported, but we'll include it anyway.
                props[name] = prop_id
        return props

    def get_current_props_values(self):
        import cv2
        props_map = self.query_available_props()
        values = {}
        for name, prop_id in props_map.items():
            values[name] = self.get_hardware_prop(prop_id)
        return values

    def get_raw_bgr_frame(self):
        with self._lock:
            if self._latest_raw_bgr is not None:
                return self._latest_raw_bgr.copy()
        return None

    def get_enhanced_bgr_frame(self):
        with self._lock:
            if self._latest_enhanced_bgr is not None:
                return self._latest_enhanced_bgr.copy()
            elif self._latest_raw_bgr is not None:
                return self._latest_raw_bgr.copy()
        return None

    def get_raw_jpeg(self):
        import cv2
        frame = self.get_raw_bgr_frame()
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        return None

    def get_enhanced_jpeg(self):
        import cv2
        frame = self.get_enhanced_bgr_frame()
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        return None

    def _apply_enhancements(self, cv2, np, frame):
        """Apply software enhancements based on options."""
        enhanced = frame.copy()
        
        # Software Brightness/Contrast
        alpha = self._options.get("enhance_contrast", 1.0)
        beta = self._options.get("enhance_brightness", 0.0)
        if alpha != 1.0 or beta != 0.0:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=alpha, beta=beta)

        # CLAHE
        if self._clahe is not None:
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            lab[...,0] = self._clahe.apply(lab[...,0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # Sharpen
        if self._sharpen_kernel is not None:
            enhanced = cv2.filter2D(enhanced, -1, self._sharpen_kernel)

        return enhanced

    def _capture_loop(self):
        import cv2
        import numpy as np
        
        self._init_enhancers(cv2, np)
        
        # On windows we use DSHOW for better control sometimes, but auto is fine for general
        self._cap = cv2.VideoCapture(self.index)
        
        if not self._cap.isOpened():
            _LOGGER.error(f"Cannot open camera {self.index}")
            return
            
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)

        while not self._stop_event.is_set():
            if not self.is_running:
                # Polling pause logic handled via threading to save CPU
                time.sleep(1)
                continue

            ret, frame = self._cap.read()
            if not ret:
                _LOGGER.debug(f"Failed to read frame from camera {self.index}")
                time.sleep(0.1)
                continue

            # Apply enhancements
            enhanced = self._apply_enhancements(cv2, np, frame)

            with self._lock:
                self._latest_raw_bgr = frame
                self._latest_enhanced_bgr = enhanced
