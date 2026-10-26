# Verify and reproduce the homepage media

The homepage uses saved experimental records, not new neural simulations. The current paper is [f58968795e9a325d88d478851bdb270d5389c5e5](https://github.com/Scophield/drosophila-fault-injection/tree/f58968795e9a325d88d478851bdb270d5389c5e5). Animation scientific verification remains pinned to `22999d28d8fe22f863fc8f62eaa45a57256083d0`, with original media generation at `75313d7740491e7f7830e2fc554c21e1aaefe655`; the same neural records are retained in the current paper. Main-page baseline: `8463020054538e8b9989c0ee8848047d833c4a0c`.

## Current scientific verification

Use the Python environment documented in the scientific checkout's `REPRODUCE.md`. NumPy is required for record checking; the media tools also use Pillow and Matplotlib. Python package versions are in `tools/homepage/requirements.txt`. An existing FFmpeg executable is needed only for decoding or re-encoding, not scientific verification. No whole-brain inputs, training or Brian 2 execution are required.

From the homepage checkout:

```sh
git clone --single-branch --branch artifact/iscas2027-v10.1-submission-final https://github.com/Scophield/drosophila-fault-injection.git ../science-v10.1
git -C ../science-v10.1 checkout --detach 22999d28d8fe22f863fc8f62eaa45a57256083d0
python ../science-v10.1/tools/verify_v10_1.py
python tools/homepage/verify_current.py --data-root ../science-v10.1
python tools/homepage/check_replay.py --examples docs/homepage-animation/examples.json --media media/paper-v10.1
```

`verify_current.py` verifies all 576 raw hashes and saved geometry, recalculates the reported timing/horizon counts and canonical validation-derived integer-count warnings, verifies all 288 P/R bindings and checks the five selected exports and all delivered media hashes. It does not fit parameters or run inference tests. Add `--out <new-file.json>` to save a fresh result; an existing result path is rejected.

`check_replay.py` verifies 2,472 displayed state rows and additional critical-time queries, stepped readout curves and common spatial scales. [Current result](current-verification.json) and [original replay result](../homepage-animation/replay-check.json) retain distinct generation/verification identities.

## Decode the delivered media

```sh
python tools/homepage/check_media.py --media media/paper-v10.1 --ffmpeg "<path-to-existing-ffmpeg>"
```

This decodes all four videos, checks the manifest hashes, dimensions, duration, frame counts and GIFs, and writes display-only QA files under `media/paper-v10.1/qa/`. It does not edit MP4/GIF/poster bytes or experimental records.

MP4 outputs are 1280×720, 24 fps, H.264/yuv420p with no audio; durations are 17/17/18/26 s for A/B/C/overview. GIF previews are 800×450, 8 fps and approximately 0.95/0.71/0.56/1.41 MB. The overview edits only A/B/C and adds no experiment. The homepage now embeds all four GIFs, each linked to its MP4, with separate original posters.

## Re-encode the original media

Media generation remains pinned to `75313d7740491e7f7830e2fc554c21e1aaefe655` in the archived `prepare_evidence.py` and `render.py`. The current verification proves that their 576 source records, selected geometry and displayed values are unchanged in 22999d2. Their original metadata are retained, not rewritten as a new run. Use current `verify_current.py` for canonical warning assessment.

The complete fresh-directory render recipe, FFmpeg requirements, selection rules and time mappings are in [the original generation instructions](../homepage-animation/REPRODUCE.md). Those commands explicitly obtain the separate original media-generation snapshot; they are not a substitute for the current scientific clone commands above. No external executables or system font files are distributed.

## README previews

`tools/homepage/preview_readme.py` renders the actual Markdown into a local GitHub-style preview, without adding CSS or JavaScript to the README. The local HTML is excluded from the publication files. Desktop/mobile screenshots validate the candidate only; actual default GitHub rendering is checked separately after authorized publication.

```sh
python tools/homepage/preview_readme.py
node tools/homepage/capture_preview.cjs "<path-to-existing-Chrome>"
```

The optional browser check requires an existing Node.js environment with Playwright. It opens only local files in an isolated Chrome process, checks 1280/390-pixel desktop/mobile widths in both themes, tests anchors and expanded posters, and plays all four local videos. It writes screenshots and a report under the local-only `preview/` directory. It neither uses the user's regular browser profile nor publishes a site. The preview renderer implements the Markdown subset used by this README; it is not a replacement for GitHub's renderer.
