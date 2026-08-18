#!/usr/bin/env python3
"""Correct executable metadata after a b3-builder run on native Windows.

NTFS does not expose POSIX execute bits to Node's stat(), so b3-builder records
files/bin entries as 644 on native Windows. Linux CI does not need this helper.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path


def normalize(package: Path) -> None:
    with zipfile.ZipFile(package, "r") as source:
        members = [(entry, source.read(entry.filename)) for entry in source.infolist()]

    changed = False
    rewritten: list[tuple[zipfile.ZipInfo, bytes]] = []
    for entry, payload in members:
        if entry.filename == "manifest.json":
            manifest = json.loads(payload)
            for item in manifest.get("files", []):
                normalized = str(item.get("path", "")).replace("\\", "/")
                if item.get("path") != normalized:
                    item["path"] = normalized
                    changed = True
                if normalized == "files/bin/u1-chopper-plot" and item.get("mode") != "755":
                    item["mode"] = "755"
                    changed = True
            payload = (json.dumps(manifest, indent=2) + "\n").encode()
        if entry.filename == "files/bin/u1-chopper-plot":
            entry.create_system = 3
            entry.external_attr = (0o100755 & 0xFFFF) << 16
        rewritten.append((entry, payload))

    if not changed:
        verify(package)
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=package.name + ".", suffix=".tmp", dir=package.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as target:
            for entry, payload in rewritten:
                target.writestr(entry, payload)
        os.replace(temporary, package)
    finally:
        temporary.unlink(missing_ok=True)
    verify(package)


def verify(package: Path) -> None:
    with zipfile.ZipFile(package, "r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        declared = {entry["path"]: entry for entry in manifest.get("files", [])}
        members = {
            name
            for name in archive.namelist()
            if name not in {"manifest.json", "manifest.json.sig"}
        }
        if set(declared) != members:
            raise ValueError("archive members and manifest files[] do not match")
        for name, entry in declared.items():
            digest = hashlib.sha256(archive.read(name)).hexdigest()
            if digest != entry.get("sha256"):
                raise ValueError(f"sha256 mismatch for {name}")
        executable = declared.get("files/bin/u1-chopper-plot", {})
        if executable.get("mode") != "755":
            raise ValueError("u1-chopper-plot is not marked executable")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: normalize_windows_b3.py PACKAGE.b3")
    normalize(Path(sys.argv[1]).resolve())
