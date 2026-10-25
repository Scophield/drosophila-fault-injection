# Final V10.1 encoding notation

This manuscript revision builds on the fixed count-warning manuscript `f78942d12fe9978353b3390f649b07a5ddb413b3` and the unchanged code/analysis implementation `d55bb27ae0f8e04ff425a76f47f86d90bd93f835`. `PUBLICATION.md` and `PUBLIC_SCOPE.json` bind the final PDF and source bytes; the enclosing Git commit supplies their fixed version identity.

The visual update period is 0.020 s, separate from the neural integration step of 0.0001 s. Half-angle, bearing, RF coordinates and Gaussian width use degrees in the manuscript. The half-angle is `(180/pi)*atan(0.05/d)`; expansion is its successive-frame difference divided by 0.020 s. Gain is the positive expansion divided by 150, multiplied by `exp(-half_angle/60)` and clipped to [0,1]. RF width is `max(30 degrees, half_angle)`; the unnormalized Gaussian, stored elevation gradient and gain give rates clipped to [0,150] Hz. There is no Gaussian density normalization factor in the implementation.

At initialization only, `previous_angle=None` selects the analytic derivative `(180/pi)*r*closing_speed/(d*d+r*r)`. Pre-cue gating sets gain to zero. Angle history is updated every frame, so the first enabled input at 100 ms uses the 80--100 ms finite difference. The actual frozen source already used the same Latin `u` symbol in both manuscript equations; this revision resolves timing and unit notation.

Code anchors are `sim_vision/closedloop_protocol.py:retinal_input`, `sim_vision/task_v9.py:run` and the stored RF maps. The three source files checked by the tests match all seven generating-batch snapshots. Six pure-function/record tests in `tests/test_retinal_input_formula_v10_1.py` cover initialization, the first enabled frame, degree/radian equivalence and wrapping, positive expansion and clipping, all 576 x 50 saved frames, and the frozen source identities.

The abstract calls the observations 576 test episodes organized into paired campaigns. RF-0/A/B have 24/12/12 independent test seed clusters, each with two bearings, two laws and three network conditions. Paired conditions within a seed are not independent samples. No neural record, calibration, registration, analysis result, threshold, approved figure, or Blender asset was changed.

Validation commands, using the environment in `REPRODUCE.md`:

```text
python -m unittest discover -s tests -p "test_*v10*.py" -v
python tools/verify_v10_1.py
```
