import ctypes
from ctypes import wintypes
import logging
import threading
import time
from typing import Callable

logger = logging.getLogger("PhysicalGuard")

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14

LLMHF_INJECTED = 0x00000001
LLKHF_INJECTED = 0x00000010

WM_LBUTTONDOWN = 0x0201
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_Q = 0x51

ULONG_PTR = wintypes.WPARAM
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class PhysicalInputGuard:
    """
    Guarda Físico Anti-Auto-Clique e Kill Switch:
    - Rastreia último clique físico vs injetado via WH_MOUSE_LL (LLMHF_INJECTED).
    - Detecta atalho de emergência físico Ctrl + Alt + Shift + Q via WH_KEYBOARD_LL.
    """

    def __init__(self, on_kill_switch_cb: Callable[[], None] | None = None):
        self.on_kill_switch_cb = on_kill_switch_cb
        self.last_physical_click_ts: float = 0.0
        self.last_injected_click_ts: float = 0.0

        self.mouse_hook = None
        self.keyboard_hook = None
        self.thread: threading.Thread | None = None
        self.is_running = False

        self._mouse_proc = None
        self._kb_proc = None

    def is_recent_physical_click(self, window_ms: float = 800.0) -> bool:
        """
        Retorna True APENAS se houve clique físico real no mouse do Host
        nos últimos window_ms (800ms) e POSTERIOR a qualquer clique injetado remotamente.
        """
        now = time.time()
        elapsed_ms = (now - self.last_physical_click_ts) * 1000.0
        if elapsed_ms > window_ms:
            return False
        # Se um clique injetado ocorreu no mesmo intervalo ou depois do clique físico, rejeita
        if self.last_injected_click_ts >= self.last_physical_click_ts:
            return False
        return True

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._run_hook_loop, daemon=True)
        self.thread.start()

    def _run_hook_loop(self):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        def mouse_callback(nCode, wParam, lParam):
            if nCode >= 0 and wParam == WM_LBUTTONDOWN:
                info = MSLLHOOKSTRUCT.from_address(lParam)
                is_injected = (info.flags & LLMHF_INJECTED) != 0
                now = time.time()
                if is_injected:
                    self.last_injected_click_ts = now
                else:
                    self.last_physical_click_ts = now
            return user32.CallNextHookEx(self.mouse_hook, nCode, wParam, lParam)

        def keyboard_callback(nCode, wParam, lParam):
            if nCode >= 0 and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                info = KBDLLHOOKSTRUCT.from_address(lParam)
                is_injected = (info.flags & LLKHF_INJECTED) != 0

                # Só avalia se for tecla física humana
                if not is_injected:
                    # Detectar Ctrl + Alt + Shift + Q
                    if info.vkCode == VK_Q:
                        ctrl_pressed = (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0
                        alt_pressed = (user32.GetAsyncKeyState(VK_MENU) & 0x8000) != 0
                        shift_pressed = (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0

                        if ctrl_pressed and alt_pressed and shift_pressed:
                            logger.warning("🚨 KILL SWITCH FÍSICO ACIONADO: Ctrl + Alt + Shift + Q!")
                            if self.on_kill_switch_cb:
                                self.on_kill_switch_cb()

            return user32.CallNextHookEx(self.keyboard_hook, nCode, wParam, lParam)

        self._mouse_proc = HOOKPROC(mouse_callback)
        self._kb_proc = HOOKPROC(keyboard_callback)

        self.mouse_hook = user32.SetWindowsHookExW(
            WH_MOUSE_LL, self._mouse_proc, kernel32.GetModuleHandleW(None), 0
        )
        self.keyboard_hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._kb_proc, kernel32.GetModuleHandleW(None), 0
        )

        msg = wintypes.MSG()
        while self.is_running and user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        if self.mouse_hook:
            user32.UnhookWindowsHookEx(self.mouse_hook)
        if self.keyboard_hook:
            user32.UnhookWindowsHookEx(self.keyboard_hook)

    def stop(self):
        self.is_running = False
        ctypes.windll.user32.PostQuitMessage(0)
