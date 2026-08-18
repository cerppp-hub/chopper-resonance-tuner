# Changelog

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
