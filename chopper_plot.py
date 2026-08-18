#!/usr/bin/env python3
"""Create Snapmaker U1 chopper-tuning reports without third-party packages.

Derived from MRX8024/chopper-resonance-tuner's Plotly/Numpy plotter.  The U1
package deliberately uses only Python's standard library so Bespok3d does not
need to modify the printer's system Python environment.
"""

# Copyright (C) 2024 Alexander Fedorov <altzbox@gmail.com>
# Copyright (C) 2024 Maksim Bolgov <maksim8024@gmail.com>
# Copyright (C) 2026 Snapmaker U1 adaptation contributors
# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import csv
import html
import math
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RESULTS_FOLDER = Path(
    os.environ.get(
        "U1_CHOPPER_RESULTS",
        "/userdata/gcodes/shaper_calibrate/chopper_magnitude",
    )
).expanduser()
DATA_FOLDER = Path(os.environ.get("U1_CHOPPER_TMP", "/tmp")).expanduser()
CUTOFF_RANGE = 5
COLORS = (
    "#64748b",
    "#2f4f4f",
    "#12b57f",
    "#9db512",
    "#df8816",
    "#1297b5",
    "#5912b5",
    "#b51284",
    "#127d0c",
)


def parse_arguments(arguments: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for argument in arguments:
        if "=" not in argument:
            raise ValueError(f"Expected name=value, got {argument!r}")
        name, value = argument.split("=", 1)
        parsed[name] = value
    return parsed


def read_vectors(path: Path) -> list[tuple[float, float, float]]:
    with path.open("r", encoding="utf-8", newline="") as source:
        return [
            (float(row["accel_x"]), float(row["accel_y"]), float(row["accel_z"]))
            for row in csv.DictReader(source)
        ]


def static_magnitude(path: Path) -> tuple[float, float, float]:
    vectors = read_vectors(path)
    if not vectors:
        raise ValueError(f"No accelerometer samples in {path}")
    return tuple(statistics.fmean(axis) for axis in zip(*vectors))  # type: ignore[return-value]


def median_magnitude(
    path: Path, baseline: tuple[float, float, float]
) -> float:
    vectors = read_vectors(path)
    trim = len(vectors) // CUTOFF_RANGE
    if trim:
        vectors = vectors[trim:-trim]
    if not vectors:
        raise ValueError(f"No usable accelerometer samples in {path}")
    magnitudes = [
        math.sqrt(sum((value - zero) ** 2 for value, zero in zip(vector, baseline)))
        for vector in vectors
    ]
    return statistics.median(magnitudes)


def measurement_parts(path: Path) -> tuple[str, ...] | None:
    if not path.name.endswith("__.csv") or "__" not in path.name:
        return None
    fields = path.name.split("__", 2)[1].split("_")
    return tuple(fields) if len(fields) == 9 else None


def label_for(fields: tuple[str, ...]) -> str:
    current, tbl, toff, hstrt, hend, tpfd, speed, freq, _iteration = fields
    return (
        f"current={current}_tbl={tbl}_toff={toff}_hstrt={hstrt}_hend={hend}"
        f"_tpfd={tpfd}_speed={float(speed) / 100:.2f}"
        f"_freq={float(freq) / 1000:.2f}kHz"
    )


def collect_samples(
    baseline: tuple[float, float, float], iterations: int
) -> tuple[list[tuple[str, float]], int]:
    grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)
    errors = 0
    files = sorted(DATA_FOLDER.iterdir(), key=lambda path: path.stat().st_mtime)
    for path in files:
        fields = measurement_parts(path)
        if fields is None:
            continue
        try:
            grouped[label_for(fields)].append(
                (int(fields[-1]), median_magnitude(path, baseline))
            )
        except (OSError, ValueError, KeyError):
            errors += 1

    samples: list[tuple[str, float]] = []
    for label, measurements in grouped.items():
        values = [value for _iteration, value in sorted(measurements)[:iterations]]
        if len(values) < iterations:
            errors += iterations - len(values)
        if values:
            samples.append((label, statistics.fmean(values)))
    return samples, errors


def toff_color(label: str) -> str:
    try:
        toff = int(next(part for part in label.split("_") if part.startswith("toff=")).split("=", 1)[1])
    except (StopIteration, ValueError):
        return COLORS[0]
    return COLORS[toff if 0 <= toff < len(COLORS) else 0]


def write_report(path: Path, samples: list[tuple[str, float]], title: str) -> None:
    peak = max((value for _label, value in samples), default=1.0) or 1.0
    rows = []
    for label, value in samples:
        width = max(0.25, value / peak * 100)
        escaped = html.escape(label)
        rows.append(
            '<div class="row" title="%s: %.6f">'
            '<div class="label">%s</div>'
            '<div class="track"><div class="bar" style="width:%.3f%%;background:%s"></div></div>'
            '<div class="value">%.6f</div></div>'
            % (escaped, value, escaped, width, toff_color(label), value)
        )
    document = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
body {{ margin: 24px; background: #0f172a; color: #e2e8f0; }}
h1 {{ font-size: 1.35rem; margin-bottom: 4px; }}
p {{ color: #94a3b8; margin-top: 0; }}
.chart {{ min-width: 760px; }}
.row {{ display: grid; grid-template-columns: 520px minmax(180px,1fr) 100px; gap: 12px; align-items: center; margin: 5px 0; }}
.label {{ overflow-wrap: anywhere; font: 12px ui-monospace, monospace; }}
.track {{ height: 18px; background: #1e293b; border-radius: 3px; overflow: hidden; }}
.bar {{ height: 100%; min-width: 2px; }}
.value {{ text-align: right; font: 12px ui-monospace, monospace; }}
</style></head><body><h1>{title}</h1>
<p>Lower median acceleration magnitude is better. Hover a row for its exact value.</p>
<div class="chart">{rows}</div></body></html>
""".format(title=html.escape(title), rows="\n".join(rows))
    path.write_text(document, encoding="utf-8")


def find_static_file() -> Path:
    candidates = sorted(
        DATA_FOLDER.glob("*-stand_still.csv"), key=lambda path: path.stat().st_mtime
    )
    if not candidates:
        raise FileNotFoundError("No *-stand_still.csv accelerometer baseline found")
    return candidates[-1]


def cleaner() -> int:
    removed = 0
    patterns = ("*-stand_still.csv", "*-__*.csv")
    for pattern in patterns:
        for path in DATA_FOLDER.glob(pattern):
            if path.is_file():
                path.unlink()
                removed += 1
    print(f"Removed {removed} chopper-tuning CSV file(s)")
    return 0


def main(arguments: list[str]) -> int:
    if arguments == ["cleaner"]:
        return cleaner()

    args = parse_arguments(arguments)
    driver = args.get("driver", "2240")
    iterations = int(args.get("iterations", "1"))
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    sense_resistor = round(float(args.get("sense_resistor", "12000")), 3)
    static_file = find_static_file()
    baseline = static_magnitude(static_file)
    samples, errors = collect_samples(baseline, iterations)
    if not samples:
        raise RuntimeError("No valid chopper-tuning measurement CSV files found")

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chip = static_file.name[: -len("-stand_still.csv")]
    stem = f"{chip}_tmc{driver}_{sense_resistor}_{timestamp}.html"
    reports = (
        (RESULTS_FOLDER / f"interactive_plot_{stem}", samples, "Chopper magnitude by test order"),
        (RESULTS_FOLDER / f"sorted_interactive_plot_{stem}", sorted(samples, key=lambda item: item[1]), "Chopper magnitude, lowest first"),
    )
    for path, values, title in reports:
        write_report(path, values, title)
        print(f"Report: {path}")
    if errors:
        print(f"Warning: {errors} empty, incomplete, or unreadable sample(s) detected")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        print(f"Chopper report failed: {error}", file=sys.stderr)
        raise SystemExit(1)
