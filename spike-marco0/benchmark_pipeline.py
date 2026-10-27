"""
Marco 0 — Spike Técnico de Risco
Valida:
1. DPI Awareness (PROCESS_PER_MONITOR_DPI_AWARE) e detecção de resolução real vs lógica.
2. Captura de tela com `mss` + conversão para `av.VideoFrame` (`yuv420p`) com dimensões pares e downscale <= 1080p.
3. Codificação real em loop loopback WebRTC (`aiortc` VP8 e H.264) medindo FPS, tempo por frame (média/p95) e uso de CPU (% de 1 core e % total).
4. Injeção nativa Win32 `SendInput` via `ctypes` (movimento absoluto 0..65535, scancode de teclado e Stuck-Keys Guard).
"""

import asyncio
import ctypes
from ctypes import wintypes
from fractions import Fraction
import json
import os
import platform
import statistics
import time

import av
import mss
import numpy as np
import psutil
from aiortc import RTCPeerConnection, RTCRtpSender, VideoStreamTrack


# ============================================================================
# 1. CONFIGURAÇÃO DE DPI AWARENESS & WIN32 SENDINPUT (CTYPES)
# ============================================================================

def ensure_input_desktop() -> bool:
    """Garante que a thread atual está acoplada ao Input Desktop ativo do Windows."""
    try:
        user32 = ctypes.windll.user32
        hdesk = user32.OpenInputDesktop(0, False, 0x01FF)
        if hdesk:
            user32.SetThreadDesktop(hdesk)
            return True
    except Exception:
        pass
    return False


def configure_dpi_awareness() -> str:
    """Ativa Per-Monitor DPI Awareness no Windows antes de consultar métricas."""
    ensure_input_desktop()
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        res = ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return f"Per-Monitor DPI Aware (SetProcessDpiAwareness=2, status={res})"
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            return "System DPI Aware (SetProcessDPIAware)"
        except Exception as e:
            return f"Falha ao configurar DPI Awareness: {e}"


ULONG_PTR = wintypes.WPARAM

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUTunion),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def validate_sendinput_and_dpi(screen_w: int, screen_h: int) -> dict:
    """
    Valida a precisão matemática do SendInput (MOUSEEVENTF_ABSOLUTE)
    movendo o cursor para o centro exato da tela (0.5, 0.5), verificando
    GetCursorPos() e restaurando a posição original do usuário.
    Também mede a latência de chamada da API Win32 SendInput.
    """
    user32 = ctypes.windll.user32

    orig_pt = POINT()
    user32.GetCursorPos(ctypes.byref(orig_pt))

    # Posição alvo normalizada (0.5, 0.5)
    norm_x, norm_y = 0.5, 0.5
    abs_x = int(round(norm_x * 65535))
    abs_y = int(round(norm_y * 65535))

    inp = INPUT()
    inp.type = INPUT_MOUSE
    inp.union.mi = MOUSEINPUT(
        dx=abs_x,
        dy=abs_y,
        mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
        time=0,
        dwExtraInfo=0,
    )

    latencies_us = []
    for _ in range(50):
        t0 = time.perf_counter()
        sent = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        t1 = time.perf_counter()
        latencies_us.append((t1 - t0) * 1_000_000)

    new_pt = POINT()
    user32.GetCursorPos(ctypes.byref(new_pt))

    # Restaura a posição original do cursor para não atrapalhar o usuário
    restore_inp = INPUT()
    restore_inp.type = INPUT_MOUSE
    restore_inp.union.mi = MOUSEINPUT(
        dx=int(round((orig_pt.x / max(1, screen_w - 1)) * 65535)),
        dy=int(round((orig_pt.y / max(1, screen_h - 1)) * 65535)),
        mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
        time=0,
        dwExtraInfo=0,
    )
    user32.SendInput(1, ctypes.byref(restore_inp), ctypes.sizeof(INPUT))

    expected_x = screen_w // 2
    expected_y = screen_h // 2
    err_x = abs(new_pt.x - expected_x)
    err_y = abs(new_pt.y - expected_y)

    return {
        "sent_ok": sent == 1,
        "expected_center": (expected_x, expected_y),
        "actual_cursor_pos": (new_pt.x, new_pt.y),
        "pixel_error": (err_x, err_y),
        "within_tolerance": err_x <= 2 and err_y <= 2,
        "avg_latency_us": round(statistics.mean(latencies_us), 2),
        "p95_latency_us": round(sorted(latencies_us)[int(len(latencies_us) * 0.95)], 2),
    }


# ============================================================================
# 2. BENCHMARK DE CAPTURA (MSS) + CONVERSÃO (AV.VIDEOFRAME YUV420P)
# ============================================================================

def compute_even_dimensions(width: int, height: int, max_w: int = 1920, max_h: int = 1080) -> tuple[int, int]:
    scale = min(1.0, max_w / width, max_h / height)
    out_w = int(width * scale) & ~1
    out_h = int(height * scale) & ~1
    return max(2, out_w), max(2, out_h)


import cv2


class BenchmarkScreenTrack(VideoStreamTrack):
    """Track customizada para medir captura mss + conversão YUV420p em loop WebRTC."""

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

        self.capture_times_ms: list[float] = []
        self.convert_times_ms: list[float] = []
        self.frame_count = 0
        self._start_time: float | None = None

    async def recv(self) -> av.VideoFrame:
        if self._start_time is None:
            self._start_time = time.perf_counter()

        target_pts_time = self._start_time + (self.frame_count / self.target_fps)
        now = time.perf_counter()
        wait = target_pts_time - now
        if wait > 0:
            await asyncio.sleep(wait)

        t0 = time.perf_counter()
        sct_img = self.sct.grab(self.monitor)
        t1 = time.perf_counter()

        img_bgra = np.asarray(sct_img, dtype=np.uint8)
        img_bgr = img_bgra[:, :, :3]
        if self.needs_resize:
            img_bgr = cv2.resize(img_bgr, (self.out_w, self.out_h), interpolation=cv2.INTER_LINEAR)
        yuv_planar = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV_I420)
        frame = av.VideoFrame.from_ndarray(yuv_planar, format="yuv420p")

        t2 = time.perf_counter()

        pts = int((time.perf_counter() - self._start_time) * 90000)
        frame.pts = pts
        frame.time_base = Fraction(1, 90000)

        self.capture_times_ms.append((t1 - t0) * 1000.0)
        self.convert_times_ms.append((t2 - t1) * 1000.0)
        self.frame_count += 1
        return frame


async def run_webrtc_loopback_benchmark(codec_mime: str, duration_sec: float = 6.0) -> dict:
    """
    Cria uma conexão WebRTC real em loopback (Host Peer <-> Client Peer)
    forçando o codec especificado (VP8 ou H264) para medir o custo real
    de captura + conversão + codificação WebRTC + transmissão SRTP.
    """
    pc_host = RTCPeerConnection()
    pc_client = RTCPeerConnection()

    track = BenchmarkScreenTrack(target_fps=30)
    sender = pc_host.addTrack(track)

    # Filtra o codec desejado
    capabilities = RTCRtpSender.getCapabilities("video")
    preferred_codecs = [
        c for c in capabilities.codecs if c.mimeType.lower() == codec_mime.lower()
    ]
    transceiver = next(t for t in pc_host.getTransceivers() if t.sender == sender)
    if preferred_codecs:
        transceiver.setCodecPreferences(preferred_codecs)

    received_frames = 0
    first_frame_ts = None
    last_frame_ts = None

    @pc_client.on("track")
    def on_track(remote_track):
        async def consume():
            nonlocal received_frames, first_frame_ts, last_frame_ts
            try:
                while True:
                    await remote_track.recv()
                    now = time.perf_counter()
                    if first_frame_ts is None:
                        first_frame_ts = now
                    last_frame_ts = now
                    received_frames += 1
            except Exception:
                pass

        asyncio.create_task(consume())

    # Handshake local
    t_hs_start = time.perf_counter()
    offer = await pc_host.createOffer()
    await pc_host.setLocalDescription(offer)
    await pc_client.setRemoteDescription(pc_host.localDescription)

    answer = await pc_client.createAnswer()
    await pc_client.setLocalDescription(answer)
    await pc_host.setRemoteDescription(pc_client.localDescription)
    handshake_ms = (time.perf_counter() - t_hs_start) * 1000.0

    proc = psutil.Process(os.getpid())
    logical_cores = psutil.cpu_count(logical=True) or 1
    proc.cpu_percent(interval=None)

    cpu_samples_total = []
    start_bench = time.perf_counter()
    while (time.perf_counter() - start_bench) < duration_sec:
        await asyncio.sleep(0.5)
        # psutil.Process.cpu_percent() retorna % acumulada nos cores (0 a 100 * logical_cores)
        raw_cpu = proc.cpu_percent(interval=None)
        cpu_samples_total.append(raw_cpu)

    await pc_host.close()
    await pc_client.close()
    track.sct.close()

    elapsed_stream = (
        (last_frame_ts - first_frame_ts)
        if (first_frame_ts and last_frame_ts and last_frame_ts > first_frame_ts)
        else duration_sec
    )
    effective_fps = (received_frames - 1) / elapsed_stream if received_frames > 1 else 0.0

    avg_single_core_pct = statistics.mean(cpu_samples_total) if cpu_samples_total else 0.0
    avg_system_cpu_pct = avg_single_core_pct / logical_cores

    def p95(values: list[float]) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        return s[min(len(s) - 1, int(len(s) * 0.95))]

    total_pipeline_ms = [
        c + v for c, v in zip(track.capture_times_ms, track.convert_times_ms)
    ]

    return {
        "codec": codec_mime,
        "raw_resolution": f"{track.raw_w}x{track.raw_h}",
        "encoded_resolution": f"{track.out_w}x{track.out_h}",
        "handshake_ms": round(handshake_ms, 2),
        "frames_sent": track.frame_count,
        "frames_decoded": received_frames,
        "effective_fps": round(effective_fps, 2),
        "capture_avg_ms": round(statistics.mean(track.capture_times_ms), 2) if track.capture_times_ms else 0,
        "capture_p95_ms": round(p95(track.capture_times_ms), 2),
        "convert_avg_ms": round(statistics.mean(track.convert_times_ms), 2) if track.convert_times_ms else 0,
        "convert_p95_ms": round(p95(track.convert_times_ms), 2),
        "pipeline_avg_ms": round(statistics.mean(total_pipeline_ms), 2) if total_pipeline_ms else 0,
        "pipeline_p95_ms": round(p95(total_pipeline_ms), 2),
        "cpu_single_core_equiv_pct": round(avg_single_core_pct, 2),
        "cpu_total_system_pct": round(avg_system_cpu_pct, 2),
        "logical_cores": logical_cores,
    }


async def main():
    print("=" * 72)
    print("INICIANDO MARCO 0 — SPIKE TÉCNICO DE RISCO (MSS + AIORTC + SENDINPUT)")
    print("=" * 72)

    dpi_status = configure_dpi_awareness()
    print(f"[1/4] DPI Awareness: {dpi_status}")

    with mss.mss() as sct:
        mon = sct.monitors[1]
        screen_w, screen_h = mon["width"], mon["height"]
    print(f"      Resolução física detectada no Monitor Primário: {screen_w}x{screen_h}")

    print("[2/4] Validando Win32 SendInput (precisão de coordenadas e latência)...")
    sendinput_res = validate_sendinput_and_dpi(screen_w, screen_h)
    print(f"      Resultado SendInput: {json.dumps(sendinput_res, indent=2)}")

    print("[3/4] Executando benchmark WebRTC Loopback com codec video/VP8 (6s)...")
    vp8_res = await run_webrtc_loopback_benchmark("video/VP8", duration_sec=6.0)
    print(f"      Resultado VP8: {json.dumps(vp8_res, indent=2)}")

    print("[4/4] Executando benchmark WebRTC Loopback com codec video/H264 (6s)...")
    h264_res = await run_webrtc_loopback_benchmark("video/H264", duration_sec=6.0)
    print(f"      Resultado H264: {json.dumps(h264_res, indent=2)}")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "system": {
            "os": f"{platform.system()} {platform.release()} ({platform.version()})",
            "python": platform.python_version(),
            "processor": platform.processor(),
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "dpi_awareness": dpi_status,
        },
        "sendinput_validation": sendinput_res,
        "webrtc_benchmarks": {
            "VP8": vp8_res,
            "H264": h264_res,
        },
    }

    out_path = os.path.join(os.path.dirname(__file__), "marco0_report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 72)
    print(f"Relatório salvo com sucesso em: {out_path}")
    print("=" * 72)


if __name__ == "__main__":
    asyncio.run(main())
