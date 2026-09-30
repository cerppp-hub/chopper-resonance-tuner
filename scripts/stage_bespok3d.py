#!/usr/bin/env python3
"""Assemble canonical U1 Chopper Resonance Tuner source for b3-builder."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SOURCE = REPO_ROOT / "bespok3d" / "u1-chopper-resonance-tuner"
STAGE_ROOT = REPO_ROOT / "dist" / "u1-chopper-resonance-tuner"


def stage() -> Path:
    if STAGE_ROOT.exists():
        shutil.rmtree(STAGE_ROOT)

    shutil.copytree(PACKAGE_SOURCE, STAGE_ROOT)

    extra_dir = STAGE_ROOT / "files" / "klipper" / "klippy" / "extras"
    config_dir = STAGE_ROOT / "files" / "cfg" / "klipper"
    extra_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO_ROOT / "chopper_tune.py", extra_dir)
    shutil.copy2(
        REPO_ROOT / "chopper_tune.cfg",
        config_dir / "u1-chopper-resonance-tuner.cfg",
    )
    shutil.copy2(
        REPO_ROOT / "klipper_requirements.txt",
        STAGE_ROOT / "klipper_requirements.txt",
    )

    shutil.copy2(REPO_ROOT / "LICENSE.txt", STAGE_ROOT / "doc" / "LICENSE")
    shutil.copy2(
        REPO_ROOT / "docs" / "SNAPMAKER_U1.md", STAGE_ROOT / "doc" / "README.md"
    )
    return STAGE_ROOT


if __name__ == "__main__":
    print(stage())
