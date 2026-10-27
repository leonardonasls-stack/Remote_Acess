import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from host_config import HostConfigManager
from scancode_map import get_scancode
from input_controller import InputController
from physical_guard import PhysicalInputGuard


def test_scancode_mapping():
    """Valida mapeamento de teclas comuns e ABNT2."""
    assert get_scancode("KeyA") == (0x1E, False)
    assert get_scancode("ArrowUp") == (0x48, True)  # Extended key
    assert get_scancode("IntlBackslash") == (0x56, False)  # ABNT2 barra invertida
    assert get_scancode("IntlRo") == (0x73, False)         # ABNT2 interrogação


def test_input_controller_stuck_keys_guard():
    """Valida rastreamento e liberação de teclas e botões presos."""
    controller = InputController()
    controller.pressed_mouse_buttons.add(0)  # Botão esquerdo
    controller.pressed_keys.add((0x1E, False))  # Tecla 'A'

    assert len(controller.pressed_mouse_buttons) == 1
    assert len(controller.pressed_keys) == 1

    # Ao alternar para modo visualização, release_all deve limpar o conjunto
    controller.set_mode("view")
    assert len(controller.pressed_mouse_buttons) == 0
    assert len(controller.pressed_keys) == 0


def test_physical_guard_click_detection():
    """Valida janela de 800ms e rejeição de auto-clique injetado."""
    guard = PhysicalInputGuard()

    # Sem cliques: deve ser False
    assert not guard.is_recent_physical_click()

    # Simular clique injetado recente: deve ser rejeitado
    guard.last_injected_click_ts = 1000.0
    guard.last_physical_click_ts = 999.0
    assert not guard.is_recent_physical_click()
