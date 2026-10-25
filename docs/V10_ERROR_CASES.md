# Executed V10 integrity challenges

Canonical report: `audit/v10/evidence-05/check.json`. All cases below are copied-record diagnostics, not independent neural experiments or randomly sampled errors. The same generic checker and each native adapter were used.

| Adapter | Predefined corruption | Detected | Issue codes |
|---|---|---:|---|
| tank | missing paired condition | True | matrix-membership |
| tank | duplicate trial replacing a condition | True | duplicate-cell, matrix-membership |
| tank | swapped source/config/map/calibration binding | True | mixed-bindings |
| tank | same seed label but different shared input stream | True | adapter-replay, unpaired-uniforms |
| tank | fault mask changed across laws/bearings | True | adapter-pair-replay, unpaired-mask |
| tank | milliseconds mislabelled as seconds | True | decision-availability, frame-clock |
| tank | truncated resource exposure | True | incomplete-exposure |
| tank | decreasing cumulative resource | True | resource-accounting |
| tank | decision used before it exists | True | decision-availability |
| tank | nonfinite decision time | True | invalid-frame-schema |
| tank | success despite a recorded failure | True | outcome-label |
| tank | missing native measurement field | True | adapter-replay |
| tank | rounded delayed actuation to frame boundary | True | adapter-replay |
| tank | same-frame applied control | True | adapter-replay |
| fly | missing paired condition | True | matrix-membership |
| fly | duplicate trial replacing a condition | True | duplicate-cell, matrix-membership |
| fly | swapped source/config/map/calibration binding | True | mixed-bindings |
| fly | same seed label but different shared input stream | True | unpaired-uniforms |
| fly | fault mask changed across laws/bearings | True | adapter-pair-replay, unpaired-mask |
| fly | milliseconds mislabelled as seconds | True | decision-availability, frame-clock |
| fly | truncated resource exposure | True | incomplete-exposure |
| fly | decreasing cumulative resource | True | resource-accounting |
| fly | decision used before it exists | True | decision-availability |
| fly | nonfinite decision time | True | invalid-frame-schema |
| fly | success despite a recorded failure | True | outcome-label |
| fly | missing native smoothing field | True | adapter-replay |
| fly | wrong exact-horizon burst flag | True | adapter-replay |
| fly | altered body-frame bearing | True | adapter-replay |

All 14 selected types per adapter were detected. This is 28 instantiated cases, not 28 independent error types or exhaustive fault coverage. The clean inputs were the retained 288-record neural baseline and 96 actual delayed-tank episodes. Five additional source/calibration-manifest regressions are unit tests, not extra scientific samples.

The explicitly synthetic, untrusted zero-neural-readout logger passes input/plant replay without neural equations. Its summary and hash are retained in the canonical report; it is never stored among scientific episodes or used for inference. Thus these checks cannot authenticate execution or unlogged neural state. They also cannot establish physical model validity, biological RF accuracy, real upset rates or hardware energy/area.

The read-only historical probe `audit/v10/legacy-timing-01/check.json` independently examines 72 archived V8 records. Its complete discrepancy lists include 6 exact-horizon flag errors and 17 nominal/realized delay discrepancies. These are actual archived examples of clock error types, not mutations of new RF tests. V8 uses a different protocol and is not pooled with V9/V10.

The controlled all-sensor-dropout unit fixture exercises a genuine within-segment tank boundary crossing and verifies rejection of an altered failure time. It is an explicitly controlled fixture, not an extra Monte Carlo sample. All 96 nominal tank example episodes remain safe; no tolerance superiority is inferred.
