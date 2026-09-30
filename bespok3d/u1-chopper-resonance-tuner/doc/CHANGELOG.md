# Changelog

## 0.2.0-u1.0 - 2026-09-30

- Rebase the plugin on eoyilmaz's CoreXY motor-isolation fork at commit
  `7e95549c2863b86340aba6eab35c8635675e0584`.
- Replace the macro, shell-command bridge, and external CSV plotter with the
  native `chopper_tune.py` Klipper extension.
- Support the firmware 1.6+/2.0 `sensor_accelerometer_identify` wrapper and
  either detected LIS2DW or SC7A20, while retaining the legacy direct sensor.
- Detect stock 200-step or upgraded 400-step motors and reject mismatched X/Y
  CoreXY motor resolutions.
- Preserve explicit TMC Autotune current, TBL, TOFF, HSTRT, HEND, and TPFD
  settings in resonance discovery; leave MRES, INTPOL, and DEDGE untouched.
- Use the U1's 12.5 MHz TMC2240 clock, keep a one-millimetre travel boundary,
  restrict tuning to X/Y, and disable automatic `printer.cfg` writes by
  default.
- Bake NumPy, SciPy, and Plotly as reversible Klipper Python dependencies and
  save output in the U1's gcode-visible storage.

## 0.1.0-u1.3 - 2026-08-16

- Let explicit chopper fields override static `printer.cfg` defaults in vibration-discovery mode, so a run can preserve values applied dynamically by TMC Autotune.
- Include TPFD in the discovery startup message and allow a single `TPFD_MIN` value to pin that field.

## 0.1.0-u1.2 - 2026-08-16

- Keep one millimetre of margin when automatically sizing a vibration sweep, avoiding a floating-point boundary failure on the U1's 251 mm usable X span with 400-step motors.
- Clarify that 0.9-degree LDO X/Y motors require `full_steps_per_rotation: 400` on both CoreXY steppers.

## 0.1.0-u1.1 - 2026-08-16

- Package upstream commit `1f98212ca9dbfdf15d516115dd4c26e97b914a8d` for Bespok3d and the Snapmaker U1 vendor Klipper layout.
- Limit calibration to the U1's paired CoreXY TMC2240 X/Y motors; Z and the four toolhead extruders are never tuned.
- Select the stock `e0_lis2dw` accelerometer correctly from the U1's `lis2dw e0_lis2dw` resonance configuration.
- Use the U1 TMC2240's 12.5 MHz clock when calculating chopper frequency.
- Replace the upstream NumPy, tqdm, Plotly, apt, pip, and venv requirements with a dependency-free standalone HTML report generator.
- Restrict temporary-file cleanup to this tool's own accelerometer CSV naming patterns.
- Add compatibility tests, staging automation, attribution, and U1-specific safety and recovery instructions.
