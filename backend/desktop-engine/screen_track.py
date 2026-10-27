import asyncio
from fractions import Fraction
import time
import av
import cv2
import mss
import numpy as np
from aiortc import VideoStreamTrack
import ctypes


def ensure_input_desktop() -> bool:
    """Garante que a thread de captura esteja conectada à área de trabalho ativa."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return True
    except Exception:
        pass
    return False


def compute_even_dimensions(width: int, height: int, max_w: int = 1920, max_h: int = 1080) -> tuple[int, int]:
    scale = min(1.0, max_w / width, max_h / height)
    out_w = int(width * scale) & ~1
    out_h = int(height * scale) & ~1
    return max(2, out_w), max(2, out_h)


class ScreenStreamTrack(VideoStreamTrack):
    """
    Captura o monitor primário com `mss` e converte para `av.VideoFrame` (YUV420p)
    com limitação a 30 FPS e clock de 90 kHz.
    """

    kind = "video"

    def __init__(self, target_fps: int = 30):
        super().__init__()
        self.target_fps = target_fps
        ensure_input_desktop()
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]
        self.raw_w = self.monitor["width"]
        self.raw_h = self.monitor["height"]
        self.out_w, self.out_h = compute_even_dimensions(self.raw_w, self.raw_h)
        self.needs_resize = (self.out_w != self.raw_w) or (self.out_h != self.raw_h)

        self.frame_count = 0
        self._start_time: float | None = None

    async def recv(self) -> av.VideoFrame:
        if self._start_time is None:
            self._start_time = time.perf_counter()

        # Pacing exato para target_fps
        target_pts_time = self._start_time + (self.frame_count / self.target_fps)
        now = time.perf_counter()
        wait = target_pts_time - now
        if wait > 0:
            await asyncio.sleep(wait)

        # Captura GDI em memória
        sct_img = self.sct.grab(self.monitor)
        img_bgra = np.asarray(sct_img, dtype=np.uint8)
        img_bgr = img_bgra[:, :, :3]

        if self.needs_resize:
            img_bgr = cv2.resize(img_bgr, (self.out_w, self.out_h), interpolation=cv2.INTER_LINEAR)

        # Conversão direta e ultrarrápida para YUV420 planar
        yuv_planar = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV_I420)
        frame = av.VideoFrame.from_ndarray(yuv_planar, format="yuv420p")

        pts = int((time.perf_counter() - self._start_time) * 90000)
        frame.pts = pts
        frame.time_base = Fraction(1, 90000)
        self.frame_count += 1
        return frame

    def close(self):
        try:
            self.sct.close()
        except Exception:
            pass
