from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLATPAK_SETUP = ROOT / "files/usr/libexec/universal-lite-flatpak-setup"
FLATPAK_INSTALL_SERVICE = (
    ROOT / "files/usr/lib/systemd/system/universal-lite-flatpak-install.service"
)
SKIP_MARKER = "/var/lib/universal-lite/flatpak-setup.skip"


def test_initial_install_completion_checks_apps_and_runtimes():
    script = FLATPAK_SETUP.read_text()

    assert "flatpak list --system --columns=application" in script
    assert "flatpak list --system --app --columns=application" not in script


def test_flatpak_install_service_is_gated_by_skip_marker():
    service = FLATPAK_INSTALL_SERVICE.read_text()

    assert f"ConditionPathExists=!{SKIP_MARKER}" in service


def test_flatpak_setup_script_honors_skip_marker_before_network_work():
    script = FLATPAK_SETUP.read_text()
    skip_definition = f"SKIP_STAMP={SKIP_MARKER}"
    skip_check = 'if [ -f "$SKIP_STAMP" ]; then'

    assert skip_definition in script
    assert skip_check in script
    assert script.index(skip_check) < script.index("if [ -f \"$STAMP\" ]; then")
