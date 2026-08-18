# Snapmaker U1 installation and safety guide

This branch packages Chopper Resonance Tuner for a Snapmaker U1 through
Bespok3d. Do not run upstream `install.sh` on the printer: its Raspberry
Pi-style paths, apt commands, and pip/venv setup do not match the U1 appliance.

## Scope

- Motion: CoreXY X and Y, whose TMC2240 drivers are tuned together. Upgraded
  LDO-42STH48-2504MACF 0.9-degree motors are supported when both `[stepper_x]`
  and `[stepper_y]` declare `full_steps_per_rotation: 400`.
- Z: not supported and never modified.
- Toolhead extruders: not supported and never modified.
- Accelerometer: the stock `lis2dw e0_lis2dw` configuration; the macro passes
  its Klipper mux name, `e0_lis2dw`.
- Driver clock: 12.5 MHz, matching the U1 Klipper TMC2240 implementation.
- Reports: standalone HTML under
  `/userdata/gcodes/shaper_calibrate/chopper_magnitude`.

The package installs one Klipper extra, one Klipper config fragment, and one
system executable. It does not install apt packages, wheels, a venv, or a
Moonraker update manager.

## Important safety behavior

`CHOPPER_TUNE` repeatedly changes live TMC2240 chopper registers and can also
change motor current when explicitly requested. A completed or interrupted run
can leave the last test values active. **Restart Klipper after every run or
abort, before homing again or printing.** A restart restores the values from
the active driver configuration (and reruns TMC Autotune when that plugin is
installed).

The broad upstream register sweep can take about two hours and may consume
hundreds of megabytes in `/tmp`. Start with resonance-speed discovery and then
use narrow explicit register ranges. Never tune while a print is active.

## Prepare

1. Make sure no print is running, the bed and toolheads are cool, and the full
   X/Y travel area is clear.
2. Dock toolhead 0 so `e0_lis2dw` is present and responsive.
3. Keep access to the power switch. Listen for grinding, harsh squeal, or lost
   steps and cut power immediately if motion becomes abnormal.
4. Record the starting state:

   ```gcode
   DUMP_TMC STEPPER=stepper_x
   DUMP_TMC STEPPER=stepper_y
   ```

## Install

1. In Bespok3d Desktop, drag in
   `u1-chopper-resonance-tuner-0.1.0-u1.3.b3`.
2. Review the permissions: one Klipper extra, one config fragment, one system
   executable, and a Klipper restart.
3. Install it and wait for Klipper to report **Ready**.
4. Confirm `CHOPPER_TUNE` appears in the web console.

## Calibrate conservatively

Discover resonant speeds separately for each movement axis:

```gcode
CHOPPER_TUNE AXIS=X FIND_VIBRATIONS=1
```

If TMC Autotune is installed, its live register values are not visible through
Klipper's static configuration object. Read the live values with `DUMP_TMC`,
then pin them explicitly during discovery. Only each `_MIN` parameter is needed
when testing one fixed value. For the LDO profile with TBL=1, TOFF=5, HSTRT=7,
HEND=9, and TPFD=2, use:

```gcode
CHOPPER_TUNE AXIS=X FIND_VIBRATIONS=1 TBL_MIN=1 TOFF_MIN=5 HSTRT_MIN=7 HEND_MIN=9 TPFD_MIN=2
```

The tuner does not write MRES, INTPOL, or DEDGE, so the live values established
by the active Klipper/TMC Autotune configuration remain in effect.

Restart Klipper, confirm **Ready**, then repeat with `AXIS=Y`. Download the
`sorted_interactive_plot_*.html` reports from the U1 gcode storage and choose a
low resonant speed to investigate.

For the first register test, hold all fields at their configured defaults and
confirm the end-to-end workflow. The stock U1 Klipper TMC2240 defaults are
TBL=2, TOFF=3, HSTRT=5, HEND=2, and TPFD=4:

```gcode
CHOPPER_TUNE AXIS=X MIN_SPEED=55 MAX_SPEED=55 TBL_MIN=2 TBL_MAX=2 TOFF_MIN=3 TOFF_MAX=3 HSTRT_MIN=5 HSTRT_MAX=5 HEND_MIN=2 HEND_MAX=2 TPFD_MIN=4 TPFD_MAX=4
```

Restart Klipper after the report is written. Expand only one small range at a
time. Repeat for Y because X and Y movement load the shared CoreXY motors
differently, even though each test writes the paired drivers together.

## Applying a result

This package measures candidates; it intentionally does not make a winning
combination persistent. If the separate U1 TMC Autotune package is installed,
you can validate a candidate at runtime with its `AUTOTUNE_TMC` command. A raw
`SET_TMC_FIELD` write is also temporary. Persistence belongs in the
Bespok3d-managed driver/autotune configuration, not in this tuner's generated
files.

Change one field at a time, re-home carefully, and validate low-speed motion
before raising acceleration. Do not keep a combination based only on the
smallest bar: reject settings that cause unpleasant noise, driver warnings,
heat, unreliable sensorless homing, or lost steps.

## Recovery

- After a normal run: restart Klipper and confirm **Ready**.
- After an abort or web disconnect: restart Klipper before any movement.
- If Klipper will not become ready: uninstall or disable this package in
  Bespok3d; its rollback removes the owned extra, config, and executable.
- If motion is abnormal after restart: power off, inspect the mechanics, and
  compare fresh `DUMP_TMC` output with the starting record.

## Sources

- [Chopper Resonance Tuner upstream](https://github.com/MRX8024/chopper-resonance-tuner)
- [Klipper TMC2240 configuration reference](https://www.klipper3d.org/Config_Reference.html#tmc2240)
- [Bespok3d](https://bespok3d.org/)
