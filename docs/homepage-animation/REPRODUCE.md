# Re-encode the original record-linked animations

This recipe preserves the original media-generation identity `75313d7740491e7f7830e2fc554c21e1aaefe655`. For current scientific assessment at `22999d2`, use [the current verification workflow](../homepage/REPRODUCE.md). The 576 neural records and displayed geometry are unchanged between these snapshots; their identities are verified separately rather than silently substituted.

## Environment

Use an existing Python 3.12 environment with NumPy, Pillow and Matplotlib, plus an existing FFmpeg executable supporting libx264, palettegen and paletteuse. Executed package versions are listed in `tools/homepage/requirements.txt`. No executables, fonts, external connectivity tables or Blender projects are distributed or downloaded by these entries.

## Obtain the original generation snapshot

From the homepage checkout:

```sh
git clone --single-branch --branch artifact/iscas2027-v10.1-timing https://github.com/Scophield/drosophila-fault-injection.git ../media-science-v10.1
git -C ../media-science-v10.1 checkout --detach 75313d7740491e7f7830e2fc554c21e1aaefe655
```

The archived preparation/renderer entries require this exact HEAD. This is the original render provenance, not the command for obtaining the current manuscript. The original generation recipe's archived rate-based warning labels are retained; `verify_current.py` independently confirms the current canonical integer-count labels. Use that current entry for warning assessment.

## Prepare and render fresh outputs

Run from the homepage checkout, choosing output directories that do not exist:

```sh
python tools/homepage/prepare_evidence.py --data-root ../media-science-v10.1 --out output/homepage-evidence-01
python tools/homepage/render.py --examples output/homepage-evidence-01/examples.json --data-root ../media-science-v10.1 --out output/homepage-media-01 --ffmpeg "<path-to-existing-ffmpeg>"
python tools/homepage/check_replay.py --examples output/homepage-evidence-01/examples.json --media output/homepage-media-01 --out output/homepage-replay-01.json
python tools/homepage/check_media.py --media output/homepage-media-01 --ffmpeg "<path-to-existing-ffmpeg>"
```

Existing example/summary files and render directories are rejected. Outputs must be outside the frozen scientific checkout. For static inspection first, replace the render output directory with another new path and use `--posters-only` instead of `--ffmpeg`.

Preparation verifies all 576 source hashes and original geometry, all 288 P/R bindings and pre-trigger prefixes, and five selected sources with the existing independent input/plant replay. It exports deterministic selection candidates, source SHA256 values and verified original subsegments. Rendering uses these subsegments, not a replacement motion model or neural simulation.

A matches the RF-0/P mean two-dose delay vector without outcome filtering. B uses the median P-contact time among RF-0/50% law-discordant pairs. C reuses B/P. All are retrospective illustrative examples. The overview edits A/B/C only and resets the labelled simulation clock at chapter cuts.

## Geometry and clocks

Positions interpolate only inside original straight subsegments; heading remains at the segment-start value until its original update boundary. Command curves use recorded post-step samples. Contact poses freeze at the exact first contact while the observation clock can continue to 1000 ms. Static icons do not represent physical sizes or wing motion; the ring marks 50 mm center separation.

Video wall time includes pauses and slow playback; simulation time and playback factor remain visible. A/B/C last 17/17/18 s; the overview is 26 s. MP4 is H.264/yuv420p, 1280×720, 24 fps with no audio; GIFs are looping 800×450 previews. Manifest files bind media hashes, frame counts, event mappings and source identities. Actual GitHub rendering is a separate post-publication check.
