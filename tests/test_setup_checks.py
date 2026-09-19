from tink_agent import setup_checks


def test_mic_status_maps_raw_values():
    assert setup_checks.mic_status(query_fn=lambda: 3) == "authorized"
    assert setup_checks.mic_status(query_fn=lambda: 2) == "denied"
    assert setup_checks.mic_status(query_fn=lambda: 1) == "restricted"
    assert setup_checks.mic_status(query_fn=lambda: 0) == "undetermined"
    assert setup_checks.mic_status(query_fn=lambda: 99) == "undetermined"


def test_accessibility_trusted_reflects_query():
    assert setup_checks.accessibility_trusted(query_fn=lambda: True) is True
    assert setup_checks.accessibility_trusted(query_fn=lambda: False) is False


def test_request_mic_invokes_request_fn():
    calls = []
    setup_checks.request_mic(callback="cb",
                             request_fn=lambda mt, cb: calls.append((mt, cb)))
    assert calls == [("soun", "cb")]


def test_request_accessibility_invokes_prompt_fn():
    calls = []
    setup_checks.request_accessibility(prompt_fn=lambda: calls.append(1))
    assert calls == [1]


from pathlib import Path

from tink_agent.config import Config
from tink_agent.audio import DeviceNotFound

REPO = Path(__file__).resolve().parent.parent


def test_tingdisk_path_honors_explicit_name():
    assert setup_checks.tingdisk_path("/Volumes", "TINGDISK") == "/Volumes/TINGDISK"


def test_tingdisk_path_prefers_whichever_disk_is_mounted():
    fx_only = lambda p: p.endswith("FX MIC DISK")
    assert setup_checks.tingdisk_path("/Volumes", exists_fn=fx_only) == "/Volumes/FX MIC DISK"
    ting_only = lambda p: p.endswith("TINGDISK")
    assert setup_checks.tingdisk_path("/Volumes", exists_fn=ting_only) == "/Volumes/TINGDISK"


def test_tingdisk_path_defaults_to_tingdisk_when_nothing_mounted():
    assert setup_checks.tingdisk_path("/Volumes", exists_fn=lambda p: False) == "/Volumes/TINGDISK"


def test_is_tingdisk_mounted_finds_fx_mic_disk():
    fx_only = lambda p: p.endswith("FX MIC DISK")
    assert setup_checks.is_tingdisk_mounted(exists_fn=fx_only) is True


def test_mounted_disk_and_model_identify_each_name():
    fx_only = lambda p: p.endswith("FX MIC DISK")
    ting_only = lambda p: p.endswith("TINGDISK")
    assert setup_checks.mounted_disk(exists_fn=fx_only) == "FX MIC DISK"
    assert setup_checks.mic_model(exists_fn=fx_only) == "FX MIC"
    assert setup_checks.mounted_disk(exists_fn=ting_only) == "TINGDISK"
    assert setup_checks.mic_model(exists_fn=ting_only) == "Ting"
    assert setup_checks.mounted_disk(exists_fn=lambda p: False) is None
    assert setup_checks.mic_model(exists_fn=lambda p: False) is None


def test_button_names_follow_the_unit_name():
    assert setup_checks.button_names("Ting") == {"mode": "orange", "select": "green", "play": "white"}
    assert setup_checks.button_names("FX MIC") == {"mode": "orange", "select": "white", "play": "gray"}
    assert setup_checks.button_names("") == setup_checks.button_names("Ting")
    assert setup_checks.button_names(None) == setup_checks.button_names("Ting")


def test_is_tingdisk_mounted_with_explicit_path_ignores_disk_search():
    assert setup_checks.is_tingdisk_mounted("/x", exists_fn=lambda p: p == "/x") is True
    assert setup_checks.is_tingdisk_mounted("/x", exists_fn=lambda p: p != "/x") is False


def test_is_tingdisk_mounted_uses_exists_fn():
    assert setup_checks.is_tingdisk_mounted(exists_fn=lambda p: True) is True
    assert setup_checks.is_tingdisk_mounted(exists_fn=lambda p: False) is False


def test_audio_present_true_when_resolved():
    assert setup_checks.audio_present(Config(), resolve_fn=lambda name: 5) is True


def test_audio_present_false_on_devicenotfound():
    def boom(name):
        raise DeviceNotFound("nope")
    assert setup_checks.audio_present(Config(), resolve_fn=boom) is False


def test_copy_then_files_match(tmp_path):
    tingdisk = tmp_path / "TINGDISK"
    tingdisk.mkdir()
    assert setup_checks.files_match(REPO, tingdisk) is False
    setup_checks.copy_device_config(REPO, tingdisk)
    assert (tingdisk / "config.json").exists()
    assert (tingdisk / "samples" / "1.wav").exists()
    assert (tingdisk / "samples" / "4.wav").exists()
    assert setup_checks.files_match(REPO, tingdisk) is True


def test_files_match_false_on_size_diff(tmp_path):
    tingdisk = tmp_path / "TINGDISK"
    tingdisk.mkdir()
    setup_checks.copy_device_config(REPO, tingdisk)
    (tingdisk / "config.json").write_text("x")  # wrong size
    assert setup_checks.files_match(REPO, tingdisk) is False
