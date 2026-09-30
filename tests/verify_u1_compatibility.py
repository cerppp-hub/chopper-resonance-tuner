from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
U1_ROOT = Path(
    os.environ.get("U1_KLIPPER_ROOT", REPO_ROOT.parent / ".reference-u1-klipper-current")
).resolve()
U1_EXTENDED_ROOT = Path(
    os.environ.get(
        "U1_EXTENDED_ROOT", REPO_ROOT.parent / ".reference-u1-extended-2"
    )
).resolve()
PACKAGE_ROOT = REPO_ROOT / "bespok3d" / "u1-chopper-resonance-tuner"


def require_text(path: Path, fragments: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise AssertionError(f"{path} is missing required contract text: {missing}")


def compile_python() -> None:
    for path in (
        REPO_ROOT / "chopper_tune.py",
        REPO_ROOT / "scripts" / "stage_bespok3d.py",
        REPO_ROOT / "scripts" / "normalize_windows_b3.py",
    ):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def verify_manifest() -> None:
    manifest = json.loads((PACKAGE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "u1-chopper-resonance-tuner"
    assert manifest["version"] == "0.2.0-u1.0"
    assert manifest["sw_version"] == "git.7e95549+u1.0"
    assert manifest["channel"] == "experiment"
    assert manifest["install"]["restart"] == ["klipper"]
    assert manifest["requires"]["variables"] == []
    assert manifest["config"] == []
    assert manifest["provides"] == [
        {"service": "u1-chopper-resonance-tuning"}
    ]
    assert manifest["permissions"] == [
        "klipper-extra",
        "klipper-config",
        "restart",
    ]
    assert manifest["install"]["place"] == [
        {
            "class": "klipper-extra",
            "src": "files/klipper/klippy/extras/chopper_tune.py",
        },
        {
            "class": "klipper-config",
            "src": "files/cfg/klipper/u1-chopper-resonance-tuner.cfg",
        },
    ]


def verify_plugin_source() -> None:
    source = REPO_ROOT / "chopper_tune.py"
    require_text(
        source,
        (
            'config.getfloat("fclk", 12.5, above=0.0)',
            '"boundary_margin", 1.0, minval=0.0',
            '"allow_save_config", False',
            '"/userdata/gcodes/shaper_calibrate/chopper_magnitude"',
            'getattr(configured_sensor, "sensor_identified", configured_sensor)',
            'hasattr(sensor, "start_internal_client")',
            '"Snapmaker U1 chopper tuning supports AXIS=X or AXIS=Y only"',
            'if self.kinematics != "corexy"',
            '"CoreXY X/Y full_steps_per_rotation values must match: "',
            "available_distance = a_axis_max - a_axis_min - self.boundary_margin",
            "distance_epsilon = 1.0e-6",
            'tbl_min = gcmd.get_int("TBL_MIN", None)',
            'tpfd_min = gcmd.get_int("TPFD_MIN", None)',
            '"Best parameters were not written to printer.cfg. "',
            'f"TPFD       : {tpfd_min}"',
        ),
    )
    text = source.read_text(encoding="utf-8")
    assert "gcode_shell_command" not in text
    assert "RESULTS_FOLDER" not in text


def verify_plugin_config() -> None:
    require_text(
        REPO_ROOT / "chopper_tune.cfg",
        (
            "[chopper_tune]",
            "boundary_margin: 1.0",
            "fclk: 12.5",
            "results_path: /userdata/gcodes/shaper_calibrate/chopper_magnitude",
            "allow_save_config: False",
        ),
    )


def verify_u1_firmware_contract() -> None:
    require_text(
        U1_ROOT / "lava" / "printer.cfg",
        (
            "kinematics: corexy",
            "position_max: 271",
            "position_max: 335",
            "[tmc2240 stepper_x]",
            "[tmc2240 stepper_y]",
            "accel_chip: sensor_accelerometer_identify e0_accelerometer",
            "[sensor_accelerometer_identify e0_accelerometer]",
            "sensor_list: lis2dw e0_lis2dw, sc7a20 e0_sc7a20",
        ),
    )
    require_text(
        U1_ROOT / "klippy" / "extras" / "sensor_accelerometer_identify.py",
        (
            "self.sensor_identified = None",
            "self.sensor_identified = self.sensor_selected",
            "self.sensor_identified = sensor_obj",
        ),
    )
    for sensor_file in ("lis2dw.py", "sc7a20.py"):
        require_text(
            U1_ROOT / "klippy" / "extras" / sensor_file,
            ("def start_internal_client(self):",),
        )
    require_text(
        U1_ROOT / "klippy" / "extras" / "tmc2240.py",
        (
            "TMC_FREQUENCY=12500000.",
            'set_config_field(config, "toff", 3)',
            'set_config_field(config, "hstrt", 5)',
            'set_config_field(config, "hend", 2)',
            'set_config_field(config, "tbl", 2)',
            'set_config_field(config, "tpfd", 4)',
        ),
    )


def verify_extended_2_contract() -> None:
    if not U1_EXTENDED_ROOT.exists():
        return
    require_text(U1_EXTENDED_ROOT / "vars.mk", ("FIRMWARE_VERSION=2.0.0",))
    matches = []
    for path in U1_EXTENDED_ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".cfg", ".patch", ".sh", ".md"}:
            try:
                if "sensor_accelerometer_identify e0_accelerometer" in path.read_text(
                    encoding="utf-8"
                ):
                    matches.append(path)
            except UnicodeDecodeError:
                continue
    assert matches, "U1 2.0 firmware source no longer references the sensor selector"


def verify_staging() -> None:
    spec = importlib.util.spec_from_file_location(
        "stage_bespok3d", REPO_ROOT / "scripts" / "stage_bespok3d.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stage_root = module.stage()
    assert (stage_root / "manifest.json").is_file()
    assert (stage_root / "doc" / "LICENSE").is_file()
    assert (stage_root / "doc" / "README.md").is_file()
    assert (
        stage_root / "files" / "klipper" / "klippy" / "extras" / "chopper_tune.py"
    ).is_file()
    assert (
        stage_root
        / "files"
        / "cfg"
        / "klipper"
        / "u1-chopper-resonance-tuner.cfg"
    ).is_file()
    assert (stage_root / "klipper_requirements.txt").read_text(encoding="utf-8") == (
        REPO_ROOT / "klipper_requirements.txt"
    ).read_text(encoding="utf-8")
    assert not (stage_root / "requirements.txt").exists()
    assert not (stage_root / "files" / "bin").exists()


if __name__ == "__main__":
    compile_python()
    verify_manifest()
    verify_plugin_source()
    verify_plugin_config()
    verify_u1_firmware_contract()
    verify_extended_2_contract()
    verify_staging()
    print("Snapmaker U1 1.6+/2.0 Chopper Resonance Tuner contract verified")
