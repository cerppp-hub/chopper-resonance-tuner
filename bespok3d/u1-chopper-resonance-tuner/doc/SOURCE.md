# Source and redistribution

The preferred form for modifying this package is the public
[`snapmaker-u1`](https://github.com/cerppp-hub/chopper-resonance-tuner/tree/snapmaker-u1)
branch. The root `chopper_tune.cfg`, `chopper_plot.py`, and
`gcode_shell_command.py` files are the canonical packaged source. The
`scripts/stage_bespok3d.py` script assembles them with the Bespok3d manifest,
documentation, and GPL text.

The adaptation is based on upstream commit
`1f98212ca9dbfdf15d516115dd4c26e97b914a8d` from:

https://github.com/MRX8024/chopper-resonance-tuner

The U1 report generator is derived from upstream `chopper_plot.py` but replaces
NumPy, tqdm, and Plotly with Python standard-library CSV processing and a
self-contained HTML report. The package is distributed under GPL-3.0-only.
Redistributors must preserve copyright and modification notices, provide
corresponding source, and state further changes.
