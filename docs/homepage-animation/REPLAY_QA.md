# Record-to-animation replay verification

Checked 2026-10-25 against fixed scientific commit `75313d7740491e7f7830e2fc554c21e1aaefe655`. This is a verification of exported frame states, timing and renderer logic; it is separate from media decoding and browser playback checks.

## Complete frame-state comparison

| Clip | Frames | State rows | Final simulation clock | Frames held at 1000 ms |
|---|---:|---:|---:|---:|
| demo-a-delay | 408 | 1224 | 1000 ms | 67 |
| demo-b-control | 408 | 816 | 1000 ms | 24 |
| demo-c-horizon | 432 | 432 | 1000 ms | 24 |

All **2472 state rows** agree with an independent affine evaluation of the selected original event segments. Maximum position discrepancy is 0 m; maximum heading discrepancy is 0 degrees. All frame numbers, wall clocks, playback rates and piecewise wall-to-simulation mappings agree with the render manifest. Each control-comparison frame uses one shared simulation clock.

## Verified display rules

- Contact poses are clamped at each source record's exact first contact. Every displayed latched-contact state has center separation 0.05 m; no counterfactual post-contact suffix motion is displayed. Noncontact trajectories continue to their stated endpoint.
- Headings remain at original segment-start values, changing at original segment boundaries; motion does not interpolate a new heading model.
- An additional 15,011 sampled/critical state evaluations match the exported segments exactly. Their 15,011 readout-rate checks select the last available frame-end sample, without rate interpolation. Thirty captured curve paths also match independently constructed post-step segments, clipped at first contact.
- The B pair shares source condition, mask, variates, input map, calibration and trigger/burst schedule: 200/450/900 ms. Its P first contact is 964.119568 ms; R has no contact through 1000 ms. These are complete feedback configurations, not a controlled isolation of one tolerance mechanism.
- C reuses that same P record. The 900-ms pause precedes contact, and the displayed 1000-ms endpoint is reached and held before the video ends. The labels describe a finite observation window and do not use permanent-escape language.
- Within each A/B comparison, all panels use equal-sized scene viewports and common world bounds. One isotropic data-to-pixel scale defines both position axes and the 50-mm ring. The 50-mm radius maps to 30.75 px in A and 33.75 px in B/C because the panels have different allocated sizes across videos; within each comparison its scale is identical. Grid labels are millimetres. Static fly/threat icons have no physical-size or wing-motion interpretation.
- Condition names, source context, simulation clock and playback factor remain visible in all renderer branches. A/B/C chapter titles distinguish the overview's independently edited segments.

## Selection and scientific scope

Examples match `examples.json` and their five replay-file hashes. A uses the recorded deterministic nearest-delay-vector rule over all 48 RF-0/P contexts without outcome filtering; B selects the median-contact case among the 11 RF-0/50% P/R outcome discordances; C reuses B/P. They remain labelled illustrative examples. Cohort summaries and warning confusion matrices remain separate all-record products.

The renderer and all data remain unchanged by this verification. This report does not assert GitHub page rendering or autonomous neural-execution authenticity. At GIF size the 24-px condition names remain the main reading anchors; 14-px auxiliary numeric labels are best read through the supplied full-size video/poster links.

## Reproduce this check

From the repository root, with the renderer dependencies installed:

```sh
python tools/homepage/check_replay.py --examples docs/homepage-animation/examples.json --media media/paper-v10.1
```

The check is read-only and prints a JSON result. To save a separate result, add `--out path/to/fresh-result.json`; an existing output path is rejected. No media, exported data or source records are modified. The verified overview manifest specifies 624 frames at 24 fps (26 seconds); decoding is checked separately.

Renderer SHA256: `d298701dc520ce90a045f733a10197938988e85af96fb908631818a78dc362fe`.
Example manifest SHA256: `cd7f3968d64106de21ec934bb7d934f3bb19a9ef895adbc9889453640b345e2f`.
