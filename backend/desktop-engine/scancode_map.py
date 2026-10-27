"""
Mapeamento de KeyboardEvent.code (W3C standard) para Hardware Scancode Set 1 do Windows.
Retorna tupla: (scancode: int, is_extended: bool).
Suporta US Standard e ABNT2 (IntlBackslash, IntlRo).
"""

KEY_TO_SCANCODE: dict[str, tuple[int, bool]] = {
    # Letras A-Z
    "KeyA": (0x1E, False),
    "KeyB": (0x30, False),
    "KeyC": (0x2E, False),
    "KeyD": (0x20, False),
    "KeyE": (0x12, False),
    "KeyF": (0x21, False),
    "KeyG": (0x22, False),
    "KeyH": (0x23, False),
    "KeyI": (0x17, False),
    "KeyJ": (0x24, False),
    "KeyK": (0x25, False),
    "KeyL": (0x26, False),
    "KeyM": (0x32, False),
    "KeyN": (0x31, False),
    "KeyO": (0x18, False),
    "KeyP": (0x19, False),
    "KeyQ": (0x10, False),
    "KeyR": (0x13, False),
    "KeyS": (0x1F, False),
    "KeyT": (0x14, False),
    "KeyU": (0x16, False),
    "KeyV": (0x2F, False),
    "KeyW": (0x11, False),
    "KeyX": (0x2D, False),
    "KeyY": (0x15, False),
    "KeyZ": (0x2C, False),

    # Linha numérica
    "Digit1": (0x02, False),
    "Digit2": (0x03, False),
    "Digit3": (0x04, False),
    "Digit4": (0x05, False),
    "Digit5": (0x06, False),
    "Digit6": (0x07, False),
    "Digit7": (0x08, False),
    "Digit8": (0x09, False),
    "Digit9": (0x0A, False),
    "Digit0": (0x0B, False),

    # Teclas de controle e navegação
    "Escape": (0x01, False),
    "Backspace": (0x0E, False),
    "Tab": (0x0F, False),
    "Enter": (0x1C, False),
    "Space": (0x39, False),
    "CapsLock": (0x3A, False),

    # Modificadores
    "ShiftLeft": (0x2A, False),
    "ShiftRight": (0x36, False),
    "ControlLeft": (0x1D, False),
    "ControlRight": (0x1D, True),  # Extended
    "AltLeft": (0x38, False),
    "AltRight": (0x38, True),     # AltGr / Extended
    "MetaLeft": (0x5B, True),     # Win Left
    "MetaRight": (0x5C, True),    # Win Right
    "ContextMenu": (0x5D, True),

    # Setas e Bloco de Navegação (Extended)
    "Insert": (0x52, True),
    "Delete": (0x53, True),
    "Home": (0x47, True),
    "End": (0x4F, True),
    "PageUp": (0x49, True),
    "PageDown": (0x51, True),
    "ArrowUp": (0x48, True),
    "ArrowLeft": (0x4B, True),
    "ArrowDown": (0x50, True),
    "ArrowRight": (0x4D, True),

    # Teclas F1 - F12
    "F1": (0x3B, False),
    "F2": (0x3C, False),
    "F3": (0x3D, False),
    "F4": (0x3E, False),
    "F5": (0x3F, False),
    "F6": (0x40, False),
    "F7": (0x41, False),
    "F8": (0x42, False),
    "F9": (0x43, False),
    "F10": (0x44, False),
    "F11": (0x57, False),
    "F12": (0x58, False),

    # Pontuação e Símbolos
    "Minus": (0x0C, False),
    "Equal": (0x0D, False),
    "BracketLeft": (0x1A, False),
    "BracketRight": (0x1B, False),
    "Backslash": (0x2B, False),
    "Semicolon": (0x27, False),
    "Quote": (0x28, False),
    "Backquote": (0x29, False),
    "Comma": (0x33, False),
    "Period": (0x34, False),
    "Slash": (0x35, False),

    # ABNT2 específicos (Brasil)
    "IntlBackslash": (0x56, False),  # Tecla \ | ao lado do Shift esquerdo
    "IntlRo": (0x73, False),         # Tecla / ? ou Ç / ponto de interrogação no ABNT2
}


def get_scancode(code: str) -> tuple[int, bool] | None:
    """Retorna (scancode, is_extended) para um KeyboardEvent.code."""
    return KEY_TO_SCANCODE.get(code)
