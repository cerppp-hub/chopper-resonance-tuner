# Attributions and copyright notices

| Component | Copyright and author | Licence | Relationship to this package |
| --- | --- | --- | --- |
| Chopper Resonance Tuner | Copyright (C) 2024 Alexander Fedorov and Maksim Bolgov; CoreXY fork maintained by Erkan Ozgur Yilmaz | GPL-3.0-only | `chopper_tune.py`, config, tests, and user guidance are adapted from upstream commit `7e95549c2863b86340aba6eab35c8635675e0584` |
| Snapmaker U1 adaptation | Copyright (C) 2026 Snapmaker U1 adaptation contributors | GPL-3.0-only | Bespok3d packaging, U1 firmware and accelerometer compatibility, TMC Autotune safeguards, tests, and documentation |
| NumPy | NumPy Developers | BSD-3-Clause | Baked runtime dependency used for sample processing |
| SciPy | SciPy Developers | BSD-3-Clause | Baked runtime dependency used for filtering and optimization |
| Plotly.py | Plotly, Inc. | MIT | Baked runtime dependency used to generate interactive reports |

The baked dependency payload retains package metadata and licence files from
the published wheels, including notices for transitive dependencies and
libraries bundled by those wheels.
