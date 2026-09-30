# Snapmaker U1 installation and safety guide

This branch packages the CoreXY fork of Chopper Resonance Tuner for the
Snapmaker U1 through Bespok3d. It targets the stock U1 motion system and the
LDO-42STH48-2503MAC 0.9-degree X/Y upgrade on firmware 1.6 through 2.0.

Do not run upstream `install.sh` on the printer. Bespok3d owns installation,
rollback, Python dependencies, the Klipper extra, and its config include.

## Compatibility

- CoreXY X/Y only. `AXIS=X` isolates `stepper_x` (logical A) with diagonal
  motion; `AXIS=Y` isolates `stepper_y` (logical B).
- TMC2240 at the U1's 12.5 MHz driver clock.
- Stock 1.8-degree motors (Klipper default: 200 full steps/revolution).
- Upgraded 0.9-degree motors when **both** `[stepper_x]` and `[stepper_y]`
  declare `full_steps_per_rotation: 400`.
- Firmware 1.5's direct `lis2dw e0_lis2dw` name.
- Firmware 1.6+ and 2.0's
  `sensor_accelerometer_identify e0_accelerometer`, including either detected
  LIS2DW or SC7A20 hardware.

The tuner refuses Z, mismatched X/Y motor resolutions, unsupported
kinematics, an unidentified sensor, or a missing supported TMC driver.

## Safety behavior

`CHOPPER_TUNE` changes one CoreXY motor driver's live current and chopper
registers while it measures. A completed or interrupted run can leave those
test values active. **Restart Klipper after every run or abort before homing
again or printing.** The restart restores the managed configuration and reruns
TMC Autotune when installed.

The plugin saves plots and JSON data under
`/userdata/gcodes/shaper_calibrate/chopper_magnitude`. It does not write a
winning combination into `printer.cfg` unless `allow_save_config: True` is
deliberately enabled. Keep the default `False` until a result has been reviewed
and validated.

## Before every run

1. Stop any print, cool the machine, clear the full X/Y envelope, and dock
   toolhead 0.
2. Confirm Klipper is Ready and the accelerometer responds.
3. Record both drivers with:

   ```gcode
   DUMP_TMC STEPPER=stepper_x
   DUMP_TMC STEPPER=stepper_y
   ```

4. Keep access to the power switch. Stop immediately for grinding, harsh
   squeal, lost steps, abnormal heat, or driver errors.

## Resonance discovery with the static driver config

With TMC Autotune disabled, the tuner reads `run_current`, `driver_TBL`,
`driver_TOFF`, `driver_HSTRT`, `driver_HEND`, and `driver_TPFD` from the active
TMC2240 configuration. For the LDO-42STH48-2503MAC motors, first confirm both
CoreXY steppers declare:

```ini
full_steps_per_rotation: 400
```

Then run:

```gcode
CHOPPER_TUNE AXIS=X FIND_RESONANCES=true
```

Restart Klipper after the output files are written, then repeat with
`AXIS=Y`. Check the startup summary: it should show the same current and
chopper values as the corresponding static TMC2240 section.

If TMC Autotune or another runtime tuner is enabled later, static config cannot
describe its live changes. In that case, read `DUMP_TMC` and pass
`CURRENT_MIN_MA` plus one `*_MIN` argument for each live field. `MRES`,
`INTPOL`, and `DEDGE` are never modified by this tuner.

The automatic speed calculation retains a one-millimetre boundary margin, so
it does not reproduce the former 251.00 mm floating-point travel failure.

## Narrow register tuning

Choose a low-vibration speed from discovery and start with one combination.
Copy the current and register values printed in the discovery startup summary
into this template (replace every angle-bracket value):

```gcode
CHOPPER_TUNE AXIS=X FIND_RESONANCES=false SEARCH_METHOD=progressive MIN_SPEED=<speed> MAX_SPEED=<speed> CURRENT_MIN_MA=<current> CURRENT_MAX_MA=<current> TBL_MIN=<tbl> TBL_MAX=<tbl> TOFF_MIN=<toff> TOFF_MAX=<toff> HSTRT_MIN=<hstrt> HSTRT_MAX=<hstrt> HEND_MIN=<hend> HEND_MAX=<hend> TPFD_MIN=<tpfd> TPFD_MAX=<tpfd>
```

After that succeeds, expand only small ranges and one family of fields at a
time. The upstream progressive search is much smaller than a full brute-force
sweep, but the number of measurements can still grow quickly.

Restart Klipper between X and Y and after any abort. Evaluate noise, heat,
homing reliability, and lost steps—not only the smallest graph bar—before
transferring a result into your managed TMC2240 configuration.

## Recovery

- Normal completion or abort: restart Klipper and wait for Ready.
- Sensor-identification error: dock toolhead 0, restart, and retest the
  accelerometer.
- Klipper will not become ready: disable or uninstall this Bespok3d package;
  rollback removes its extra, config, and reversible Python package links.
- Motion remains abnormal after restart: power off, inspect the mechanics, and
  compare new `DUMP_TMC` output with the record taken before tuning.

## Upstream and firmware references

- [CoreXY Chopper Resonance Tuner fork](https://github.com/eoyilmaz/chopper-resonance-tuner)
- [Snapmaker U1 Klipper](https://github.com/Snapmaker/u1-klipper)
- [Snapmaker U1 Extended Firmware](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware)
- [Bespok3d](https://bespok3d.org/)
