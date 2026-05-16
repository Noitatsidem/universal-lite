import importlib.machinery
import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "files/usr/libexec/universal-lite-chrome-early-oom"


def load_module():
    loader = importlib.machinery.SourceFileLoader("chrome_early_oom", str(SCRIPT))
    spec = importlib.util.spec_from_loader("chrome_early_oom", loader)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["chrome_early_oom"] = module
    spec.loader.exec_module(module)
    return module


def test_parse_meminfo_returns_mib_values():
    early_oom = load_module()

    values = early_oom.parse_meminfo(
        "MemTotal:        2048000 kB\n"
        "MemAvailable:     199680 kB\n"
        "SwapTotal:       2500000 kB\n"
        "SwapFree:         307200 kB\n"
    )

    assert values == {"mem_available_mib": 195, "swap_free_mib": 300}


def test_parse_meminfo_missing_fields_is_non_triggering():
    early_oom = load_module()

    values = early_oom.parse_meminfo("MemAvailable:     102400 kB\n")

    assert values == {"mem_available_mib": 100, "swap_free_mib": None}


def test_pressure_state_requires_two_consecutive_critical_samples():
    early_oom = load_module()
    state = early_oom.PressureState(required_samples=2, cooldown_seconds=60)

    first = state.record_sample(
        mem_available_mib=150,
        swap_free_mib=250,
        now=100,
    )
    second = state.record_sample(
        mem_available_mib=140,
        swap_free_mib=240,
        now=102,
    )

    assert first is False
    assert second is True


def test_pressure_state_resets_after_recovery_and_honors_cooldown():
    early_oom = load_module()
    state = early_oom.PressureState(required_samples=2, cooldown_seconds=60)

    assert state.record_sample(150, 250, now=100) is False
    assert state.record_sample(300, 250, now=102) is False
    assert state.record_sample(150, 250, now=104) is False
    assert state.record_sample(140, 240, now=106) is True
    state.mark_triggered(now=106)

    assert state.record_sample(130, 230, now=120) is False
    assert state.record_sample(120, 220, now=168) is False
    assert state.record_sample(110, 210, now=170) is True
