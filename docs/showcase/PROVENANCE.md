# Showcase sources and version boundaries

The visual homepage adds presentation assets to the preserved `c6d5189` homepage.
It does not change a paper, experiment, calibration, analysis result or original
animation. [Asset hashes](assets.json) bind the copied images to their existing
sources and identify the new schematic roadmap. No Blender render was rerun,
edited, cropped or downsampled.
HTML display widths leave the downloadable image bytes at their full resolution.

## Blender gallery

| File | Original pixels | Source and meaning |
|---|---|---|
| `media/showcase/fruit_fly.png` | 2400 × 1600 | Existing `blender_drosophila/fruit_fly.png`; procedural Blender illustration, not an anatomical scan or a biological recording. |
| `media/showcase/connectome.png` | 2400 × 1600 | Existing `blender_drosophila/connectome.png`; FlyWire v783 representative neural anchors, with an 8,500-cell background sample and selected visual-to-command graph. |
| `media/showcase/visual_pathway.png` | 2600 × 1600 | Existing `blender_drosophila/visual_pathway.png`; the same selected graph in a schematic layout. |

The gallery preserves the original studio images and their baked-in labels.
The paper uses separate, previously approved transparent exports from the same
Blender project; its locked Fig. 1 PDF is unchanged. The gallery does not replace
that figure.

The selected graph has 410 distinct cells and 1,050 selected directed connections:
104 LC4 cells, 210 LPLC2 cells, 88 distinct relay-role cells and eight descending
readout cells. Selected relay candidates overlap endpoints before deduplication.
These are a displayed subgraph, not all 138,639 model neurons or all 15,091,983
signed connection rows. Curves join representative anchors; they do not trace
measured axons or dendrites. In the schematic pathway, position is a designed
layout. Line thickness follows absolute model weight; colors identify groups,
not recorded activity. No body-to-brain registration is claimed.

The existing original `data_manifest.json` records sampling seed `20261023`,
source hashes, coordinate scaling and graph selection. The showcase does not
copy private `.blend` files, complete annotation tables or connectivity matrices.
It adds no meshes from third parties and no AI-generated visual assets.

## Quantitative engineering figure

`media/showcase/v10_1_ablation.png` is a byte-identical copy of the existing
`experiments/checker-ablation-v10_1/figure-03/v10_1_ablation.png` in the
[fixed executed engineering snapshot](https://github.com/Scophield/drosophila-fault-injection/tree/b29f08970f7749c916a472e835517547d832e6cc).
Its [source CSV](https://github.com/Scophield/drosophila-fault-injection/blob/b29f08970f7749c916a472e835517547d832e6cc/experiments/checker-ablation-v10_1/figure-03/source.csv)
and [manifest](https://github.com/Scophield/drosophila-fault-injection/blob/b29f08970f7749c916a472e835517547d832e6cc/experiments/checker-ablation-v10_1/figure-03/manifest.json)
are preserved. The tank panels show saved responses and the 150-ms actuator delay.
The added error catalogue compares A/B/C/D checker configurations; it is distinct
from the earlier 11 common plus three native development challenge types.

The catalogue includes 87 distinct corrupted inputs and 24 valid-control IDs
(20 distinct valid inputs). The full combination detects 81/87, compared with
36/87 for trusted-header checks; no valid controls are rejected. Six misses
remain. This author-designed evaluation describes the measured scope of these
two adapters, not general detection coverage, independent blind testing or
authentication of neural execution.

## Planned research vision

`media/showcase/research-vision.svg` is a new, original repository-native vector
schematic. Its simple chip, spike, steering and contact symbols illustrate the
labelled **RESEARCH VISION / PLANNED** chain: device nonidealities → spiking
dynamics → feedback/motion → task outcomes. It encodes no experimental data,
performance estimate or already-implemented device-level capability. No Blender
image was changed or substituted to make this schematic.

## Animation and paper identities

The four MP4/GIF/poster groups under `media/paper-v10.1/` are unchanged.
Their original generation manifest remains pinned to
`75313d7740491e7f7830e2fc554c21e1aaefe655`; the archived whole-cohort scientific
verification remains pinned to
`22999d28d8fe22f863fc8f62eaa45a57256083d0`.
[Example identities](../homepage-animation/examples.json) and
[replay verification](../homepage-animation/replay-check.json) retain their
original hashes and selection rules. They are not relabelled as newly run data.

The current paper, source and reproduction links point to
[f58968795e9a325d88d478851bdb270d5389c5e5](https://github.com/Scophield/drosophila-fault-injection/tree/f58968795e9a325d88d478851bdb270d5389c5e5),
on `research/v10.1-abstract-context`. That manuscript retains the same frozen
neural episodes, adds the separately executed engineering evaluation, and
updates the abstract and exposition. The paper's own fixed artifact references,
including the executed `b29f089` address, are not edited by the homepage work.
An immutable commit URL continues to identify exactly its original content.

[The pre-showcase README source](README-c6d5189.md) is preserved byte-for-byte.
It is a source archive: its original relative links have repository-root meaning.
[Historical project entries](../homepage/HISTORY.md) retain earlier protocol
identities, including the original 3.13-s animation.

## Attribution and licensing

The procedural fly and Blender render construction were produced in this
project. Neural model code is attributed to Philip Shiu and Nico Spiller; its
[upstream MIT notice](../../media/showcase/UPSTREAM_MODEL_LICENSE.txt) is retained.
Underlying FlyWire v783 connectivity is attributed to the FlyWire Consortium,
including Dorkenwald et al. (2024); the underlying v783 release declares CC BY 4.0.
Cell labels and representative coordinates originate from the FlyWire annotation
release; retain the original reconstruction, synapse and annotation citations.

The project's MIT software license does not assign a new license to third-party
tables. Source-specific permissions for transformed model tables and complete
annotation redistribution remain distinct from model-code licensing. This
showcase copies only existing rendered images and the upstream code notice.
See [the fixed third-party input account](https://github.com/Scophield/drosophila-fault-injection/blob/f58968795e9a325d88d478851bdb270d5389c5e5/docs/THIRD_PARTY_INPUTS_V10.md)
for the input-level provenance boundary.

## Local preview

Generate the README preview from this checkout:

```text
python tools/homepage/preview_readme.py --out preview/showcase
```

Open `preview/showcase/readme.html` or its dark variant locally. These pages
render the actual README with local QA styling; the README itself contains no
CSS or JavaScript. Local screenshots do not establish GitHub's live rendering.
No publication is performed by this workflow.
