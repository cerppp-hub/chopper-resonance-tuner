from __future__ import annotations

import ast
import csv
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
U1_ROOT = Path(
    os.environ.get("U1_KLIPPER_ROOT", REPO_ROOT.parent / "u1-klipper")
).resolve()
PACKAGE_ROOT = REPO_ROOT / "bespok3d" / "u1-chopper-resonance-tuner"
MACRO = REPO_ROOT / "chopper_tune.cfg"


def require_text(path: Path, fragments: tuple[str, ...]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [fragment for fragment in fragments if fragment not in text]
    if missing:
        raise AssertionError(f"{path} is missing required U1 APIs/settings: {missing}")


def compile_python() -> None:
    for filename in (
        "chopper_plot.py",
        "gcode_shell_command.py",
        "scripts/stage_bespok3d.py",
        "scripts/normalize_windows_b3.py",
    ):
        path = REPO_ROOT / filename
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def verify_manifest() -> None:
    manifest = json.loads((PACKAGE_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "u1-chopper-resonance-tuner"
    assert manifest["version"] == "0.1.0-u1.3"
    assert manifest["sw_version"] == "git.1f98212+u1.3"
    assert manifest["channel"] == "experiment"
    assert manifest["publisher"] == "PLACEHOLDER"
    assert manifest["install"]["restart"] == ["klipper"]
    assert manifest["requires"]["variables"] == []
    assert manifest["config"] == []
    classes = [entry["class"] for entry in manifest["install"]["place"]]
    assert classes == ["klipper-extra", "klipper-config", "system-bin"]
    assert set(manifest["permissions"]) == {
        "klipper-extra",
        "klipper-config",
        "system-bin",
        "restart",
    }


def verify_macro() -> None:
    text = MACRO.read_text(encoding="utf-8")
    assert not re.search(r"command:\s*~/", text)
    require_text(
        MACRO,
        (
            "variable_fclk: 12.5",
            "variable_boundary_margin: 1",
            "[respond]",
            "command: /userdata/bespok3d/bin/u1-chopper-plot",
            "Snapmaker U1 chopper tuning supports AXIS=X or AXIS=Y only",
            "Snapmaker U1 chopper tuning requires CoreXY AXIS=X or AXIS=Y",
            "{% set steppers = ['stepper_x', 'stepper_y'] %}",
            "config.resonance_tester.accel_chip.split()[-1]",
            "SET_TMC_FIELD STEPPER={stepper}",
            "SET_TMC_CURRENT STEPPER={stepper}",
            "Restart Klipper before printing",
            "{% set auto_speed_travel = maxAX - minAX - boundary_margin %}",
            "Explicit parameters therefore take priority over the static config values",
            "HSTRT=%d HEND=%d TPFD=%d",
        ),
    )
    assert "axis in ['x', 'y', 'z']" not in text
    assert "variable_drivers:" not in text


def verify_u1_contract() -> None:
    require_text(
        U1_ROOT / "lava" / "printer.cfg",
        (
            "[resonance_tester]",
            "accel_chip: lis2dw e0_lis2dw",
            "kinematics: corexy",
            "max_velocity: 500",
            "max_accel: 20000",
            "position_max: 271",
            "position_max: 335",
            "[tmc2240 stepper_x]",
            "[tmc2240 stepper_y]",
            "run_current: 1.2",
        ),
    )
    require_text(
        U1_ROOT / "klippy" / "extras" / "tmc.py",
        (
            'gcode.register_mux_command("SET_TMC_FIELD"',
            "reg_name = self.fields.lookup_register(field_name, None)",
            "reg_val = self.fields.set_field(field_name, value)",
        ),
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
            "config.getfloat('rref', 12000.",
        ),
    )
    require_text(
        U1_ROOT / "klippy" / "extras" / "adxl345.py",
        (
            'gcode.register_mux_command("ACCELEROMETER_MEASURE", "CHIP", name',
            'filename = "/tmp/%s-%s-%s.csv"',
        ),
    )
    require_text(
        REPO_ROOT / "gcode_shell_command.py",
        (
            'self.gcode.register_mux_command(',
            '"RUN_SHELL_COMMAND", "CMD", self.name,',
            "reactor.register_fd(self.proc_fd, self._process_output)",
        ),
    )


def write_csv(path: Path, rows: list[tuple[float, float, float]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow(("accel_x", "accel_y", "accel_z"))
        writer.writerows(rows)


def verify_report_generator() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        data = root / "tmp"
        reports = root / "reports"
        data.mkdir()
        write_csv(data / "lis2dw-e0_lis2dw-stand_still.csv", [(1, 2, 3)] * 10)
        write_csv(
            data / "lis2dw-e0_lis2dw-__1200_2_3_5_2_4_5500_200000_1__.csv",
            [(2, 2, 3), (3, 2, 3), (4, 2, 3), (3, 2, 3), (2, 2, 3)] * 2,
        )
        unrelated = data / "unrelated.csv"
        write_csv(unrelated, [(0, 0, 0)])
        environment = os.environ.copy()
        environment["U1_CHOPPER_TMP"] = str(data)
        environment["U1_CHOPPER_RESULTS"] = str(reports)
        subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "chopper_plot.py"),
                "iterations=1",
                "driver=2240",
                "sense_resistor=12000",
            ],
            check=True,
            env=environment,
            capture_output=True,
            text=True,
        )
        generated = sorted(reports.glob("*.html"))
        assert len(generated) == 2
        report = generated[0].read_text(encoding="utf-8")
        assert "current=1200_tbl=2_toff=3" in report
        assert "Lower median acceleration magnitude is better" in report
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "chopper_plot.py"), "cleaner"],
            check=True,
            env=environment,
            capture_output=True,
            text=True,
        )
        assert unrelated.exists()
        assert not list(data.glob("*-stand_still.csv"))
        assert not list(data.glob("*-__*.csv"))


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
    assert (stage_root / "files" / "klipper" / "klippy" / "extras" / "gcode_shell_command.py").is_file()
    assert (stage_root / "files" / "cfg" / "klipper" / "u1-chopper-resonance-tuner.cfg").is_file()
    plotter = stage_root / "files" / "bin" / "u1-chopper-plot"
    assert plotter.is_file()
    if os.name != "nt":
        assert plotter.stat().st_mode & stat.S_IXUSR
    assert not (stage_root / "requirements.txt").exists()
    assert not (stage_root / "klipper_requirements.txt").exists()


if __name__ == "__main__":
    compile_python()
    verify_manifest()
    verify_macro()
    verify_u1_contract()
    verify_report_generator()
    verify_staging()
    print("Snapmaker U1 Chopper Resonance Tuner compatibility contract verified")
