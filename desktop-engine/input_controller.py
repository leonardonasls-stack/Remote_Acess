import collections
import ctypes
from ctypes import wintypes
import time
from scancode_map import get_scancode

# ============================================================================
# Definições de Estruturas Win32 SendInput (ctypes)
# ============================================================================

ULONG_PTR = wintypes.WPARAM

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
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


class InputController:
    """
    Controlador Win32 SendInput:
    - Injeta movimentos absolutos normalizados (0.0000..1.0000 -> 0..65535).
    - Injeta botões de mouse e scroll.
    - Injeta teclas via Scancode Set 1 (ABNT2 e US).
    - Rate limiter de 200 mensagens/segundo.
    - Stuck-Keys Guard: rastreia teclas/botões e libera tudo com release_all().
    """

    def __init__(self, max_rate_per_sec: int = 200):
        self.max_rate_per_sec = max_rate_per_sec
        self.rate_window = collections.deque()
        self.mode: str = "control"  # "control" | "view"
        self.user32 = ctypes.windll.user32

        # Rastreamento de Stuck-Keys Guard
        self.pressed_mouse_buttons: set[int] = set()  # {0, 1, 2}
        self.pressed_keys: set[tuple[int, bool]] = set()  # {(scancode, is_extended)}

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == "view":
            self.release_all()

    def _check_rate_limit(self) -> bool:
        now = time.perf_counter()
        while self.rate_window and (now - self.rate_window[0]) > 1.0:
            self.rate_window.popleft()

        if len(self.rate_window) >= self.max_rate_per_sec:
            return False  # Excedeu 200 msg/s
        self.rate_window.append(now)
        return True

    def move_mouse(self, norm_x: float, norm_y: float):
        if self.mode != "control" or not self._check_rate_limit():
            return

        abs_x = max(0, min(65535, int(round(norm_x * 65535))))
        abs_y = max(0, min(65535, int(round(norm_y * 65535))))

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
        self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def mouse_button(self, button: int, is_down: bool, norm_x: float | None = None, norm_y: float | None = None):
        if self.mode != "control" or not self._check_rate_limit():
            return

        if norm_x is not None and norm_y is not None:
            self.move_mouse(norm_x, norm_y)

        # Mapeia 0=Left, 1=Middle, 2=Right
        if button == 0:
            flag = MOUSEEVENTF_LEFTDOWN if is_down else MOUSEEVENTF_LEFTUP
        elif button == 2:
            flag = MOUSEEVENTF_RIGHTDOWN if is_down else MOUSEEVENTF_RIGHTUP
        elif button == 1:
            flag = MOUSEEVENTF_MIDDLEDOWN if is_down else MOUSEEVENTF_MIDDLEUP
        else:
            return

        if is_down:
            self.pressed_mouse_buttons.add(button)
        else:
            self.pressed_mouse_buttons.discard(button)

        inp = INPUT()
        inp.type = INPUT_MOUSE
        inp.union.mi = MOUSEINPUT(
            dx=0,
            dy=0,
            mouseData=0,
            dwFlags=flag,
            time=0,
            dwExtraInfo=0,
        )
        self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def mouse_wheel(self, delta_x: int, delta_y: int):
        if self.mode != "control" or not self._check_rate_limit():
            return

        if delta_y != 0:
            inp = INPUT()
            inp.type = INPUT_MOUSE
            inp.union.mi = MOUSEINPUT(
                dx=0,
                dy=0,
                mouseData=wintypes.DWORD(delta_y),
                dwFlags=MOUSEEVENTF_WHEEL,
                time=0,
                dwExtraInfo=0,
            )
            self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def keyboard_key(self, code: str, is_down: bool):
        if self.mode != "control" or not self._check_rate_limit():
            return

        mapping = get_scancode(code)
        if not mapping:
            return

        scancode, is_extended = mapping
        flags = KEYEVENTF_SCANCODE
        if is_extended:
            flags |= KEYEVENTF_EXTENDEDKEY
        if not is_down:
            flags |= KEYEVENTF_KEYUP

        key_tuple = (scancode, is_extended)
        if is_down:
            self.pressed_keys.add(key_tuple)
        else:
            self.pressed_keys.discard(key_tuple)

        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki = KEYBDINPUT(
            wVk=0,
            wScan=wintypes.WORD(scancode),
            dwFlags=flags,
            time=0,
            dwExtraInfo=0,
        )
        self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def release_all(self):
        """Stuck-Keys Guard: libera imediatamente todas as teclas e botões presos."""
        # 1. Libera botões do mouse
        for btn in list(self.pressed_mouse_buttons):
            if btn == 0:
                flag = MOUSEEVENTF_LEFTUP
            elif btn == 2:
                flag = MOUSEEVENTF_RIGHTUP
            elif btn == 1:
                flag = MOUSEEVENTF_MIDDLEUP
            else:
                continue

            inp = INPUT()
            inp.type = INPUT_MOUSE
            inp.union.mi = MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flag, time=0, dwExtraInfo=0)
            self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        self.pressed_mouse_buttons.clear()

        # 2. Libera teclas do teclado
        for scancode, is_extended in list(self.pressed_keys):
            flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
            if is_extended:
                flags |= KEYEVENTF_EXTENDEDKEY

            inp = INPUT()
            inp.type = INPUT_KEYBOARD
            inp.union.ki = KEYBDINPUT(
                wVk=0,
                wScan=wintypes.WORD(scancode),
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            )
            self.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        self.pressed_keys.clear()
