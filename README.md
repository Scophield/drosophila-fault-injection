# Paired Fault Assessment of a Fly-Connectome Spiking Controller

This branch publishes the updated manuscript, figures, LaTeX and related Python
code. It is a paper/code snapshot; new per-trial research records and internal
audits are not included. No claim of complete saved-data reproducibility is made
for this reduced branch. The separate full local research snapshot is preserved.

## Current manuscript

- [Main PDF](paper/fly_connectome_fault_assessment_v9_blender.pdf)
- [Main LaTeX](paper/main.tex)
- [Supplement PDF](paper/fly_connectome_supplement_v9_blender.pdf)
- [Supplement LaTeX](paper/supplement.tex)

The main has four technical pages and a fifth page of references. Figure 1 uses
source-checked Blender assets with explicit selected-subgraph and schematic
limitations. Quantitative figures, experiments and estimates are unchanged.
The supplement retains its 13 pages of evidence and limitations.

The study uses 24 independent core seed clusters and separate stress/diagnostic
cohorts. One graph, assumed receptive fields, unequal healthy safety reserves,
sparse failures and no hardware mapping remain material limitations. Publication
of this paper/code branch is not a conference submission or acceptance.

## Scope and compilation

Only manuscript files and related code are updated relative to the preceding
public submission branch. Previously public historical files remain in history.
New raw records, calibration/seed matrices, audit materials, external model
inputs, runtime caches and local source ZIPs are not uploaded in this branch.
The old reproduction documents concern older public protocols and do not supply
the missing v9 records. Do not mix their data with this manuscript's protocol.

From the repository root, compile into a new staging directory:

```text
powershell -NoProfile -File tools/build_paper.ps1 -BuildDirectory audit/my-paper-build
```

A configured TeX distribution with IEEEtran and the packages in main.tex is
required. Compilation does not need the external connectome or new simulations.
The code retains its model/input dependencies; code availability alone does not
supply a complete experiment environment. See GITHUB_SNAPSHOT.md for exact PDF
hashes and publication scope. Existing CRLF/LF source bytes are preserved by
.gitattributes to avoid checksum changes from Git newline conversion.
