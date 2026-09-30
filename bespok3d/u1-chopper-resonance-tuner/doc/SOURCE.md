# Source and redistribution

The preferred form for modifying this package is the public
[`snapmaker-u1`](https://github.com/cerppp-hub/chopper-resonance-tuner/tree/snapmaker-u1)
branch. The root `chopper_tune.py` and `chopper_tune.cfg` files are the
canonical packaged source. The
`scripts/stage_bespok3d.py` script assembles them with the Bespok3d manifest,
documentation, and GPL text.

The adaptation is based on upstream commit
`7e95549c2863b86340aba6eab35c8635675e0584` from:

https://github.com/eoyilmaz/chopper-resonance-tuner

The `.b3` bakes the packages declared in `klipper_requirements.txt` for the
U1's aarch64 CPython 3.11 runtime. They are linked reversibly rather than
installed with pip on the printer. The package is distributed under
GPL-3.0-only. Redistributors must preserve copyright and modification notices,
provide corresponding source, and state further changes.
