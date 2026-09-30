# Chopper Resonance Tuner for Snapmaker U1

This branch adapts [eoyilmaz's CoreXY Chopper Resonance Tuner](https://github.com/eoyilmaz/chopper-resonance-tuner)
for reversible installation through Bespok3d on the Snapmaker U1.

It uses diagonal CoreXY motion to isolate one physical X/Y motor at a time,
captures accelerometer samples inside Klipper, searches TMC2240 chopper
settings, and writes interactive Plotly reports plus JSON measurements to the
U1's gcode-visible storage.

## U1 compatibility

- Snapmaker U1 firmware 1.6 through 2.0.
- CoreXY `stepper_x` and `stepper_y`; Z and extruder drivers are rejected.
- Stock 1.8-degree motors at 200 full steps/revolution.
- LDO-42STH48-2503MAC 0.9-degree upgrades when both X and Y declare
  `full_steps_per_rotation: 400`.
- The legacy `lis2dw e0_lis2dw` accelerometer name.
- The firmware 1.6+ `sensor_accelerometer_identify e0_accelerometer` wrapper,
  resolving either an LIS2DW or SC7A20 at runtime.
- The U1 TMC2240's 12.5 MHz clock.
- Static `run_current` and chopper values from the active TMC2240 config, plus
  optional explicit overrides for installations that use runtime tuning.

## Installation

Build or download `u1-chopper-resonance-tuner-0.2.0-u1.0.b3`, then drag it into
Bespok3d Desktop and install it on the printer. Do not use an upstream shell
installer, `apt`, or on-printer `pip`.

The package owns:

- the `chopper_tune.py` Klipper extra;
- its Klipper config include;
- reversible links for baked aarch64 NumPy, SciPy, and Plotly packages; and
- the Klipper restart needed to load or unload the extension.

Read [the full U1 installation, command, and safety guide](docs/SNAPMAKER_U1.md)
before running the tuner.

## Quick command reference

With the LDO motors configured at 400 full steps/revolution and TMC Autotune
disabled, resonance discovery reads the active static TMC2240 values directly:

```gcode
CHOPPER_TUNE AXIS=X FIND_RESONANCES=true
```

Repeat on `AXIS=Y`, restarting Klipper between runs. The tuner keeps a
one-millimetre movement margin and will not hit the former 251.00 mm automatic
travel calculation.

## Safety

The command changes live motor current and chopper registers. Restart Klipper
after every completion or abort before any print or further motion. Automatic
`printer.cfg` writes are disabled by default so the user can validate and
transfer a result deliberately.

## Development

`scripts/stage_bespok3d.py` creates the canonical Bespok3d source directory in
`dist/`. Building requires the Bespok3d builder's `--bake` mode because the
Klipper extension imports NumPy, SciPy, and Plotly.

The U1 contract test checks the current official U1 Klipper sensor selector,
both supported accelerometer drivers, the 12.5 MHz TMC clock, the extended 2.0
firmware line, staging, and package metadata:

```shell
python tests/verify_u1_compatibility.py
```

Upstream authors: Alexander Fedorov, Maksim Bolgov, and Erkan Ozgur Yilmaz.
Distributed under GPL-3.0; see [LICENSE.txt](LICENSE.txt) and the packaged
attribution document.
