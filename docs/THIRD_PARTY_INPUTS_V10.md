# Third-party inputs: provenance and licensing boundary

Checked 2026-10-23. This project's MIT LICENSE does not relicense third-party
tables, annotations, figures, or publications. Preserve each upstream notice.

| Input | Source / version used | Licensing and reproduction boundary |
|---|---|---|
| Neural model code | [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model), exercised commit `91bdd1e7dcf193f3e7ca5a8933497fcef63b7960` | Upstream [MIT license](https://github.com/philshiu/Drosophila_brain_model/blob/91bdd1e7dcf193f3e7ca5a8933497fcef63b7960/LICENSE), copyright 2023 Philip Shiu and Nico Spiller. Generating snapshots preserve model.py and the notice; this does not establish licensing of all associated datasets. |
| Completeness_783.csv / Connectivity_783.parquet | Separate sibling model checkout; exact SHA256 values in every frozen registration and generating manifest | Not bundled as a complete experimental environment. Obtain upstream inputs separately and compare exact hashes; no silent substitution of current upstream data. The model README links the [Edmond deposit](https://doi.org/10.17617/3.CZODIW). Its metadata endpoint failed certificate verification during this audit; no blanket license for these transformed table bytes was inferred. |
| Underlying FlyWire v783 connectivity | [Zenodo version 783.0](https://zenodo.org/records/10676866), DOI `10.5281/zenodo.10676866` | The retrieved primary API metadata declares `cc-by-4.0` (saved at `audit/v10/upstream-access/zenodo-metadata.json`). Cite the original reconstruction/synapse/annotation works as upstream requests. This source license alone does not prove that a particular transformed model table is byte-equivalent. |
| `sim/data/annotations.tsv` | Exact local SHA256 `d00c92142f6b96ce916cbef681d0d93f856b7cb0904c738f996130cd0e0c0b29`; already included in public V9 commit | Content matches [this fixed upstream file](https://github.com/flyconnectome/flywire_annotations/blob/a83b2776d60d5764cef36b927f5f9679c16c47a2/supplemental_files/Supplemental_file1_neuron_annotations.tsv) after **CRLF-to-LF only** normalization: upstream Git blob `02e72f6c8161d3465f77fec0edf96c5d98027a9e`. Local139,249 CRLF line endings explain the initial mismatch; original generating bytes are unchanged. Upstream README requests version-specific citations. The complete pinned repository tree has no license-named file and current GitHub repository metadata reports `license: null`; these are observed metadata, not a legal determination. Annotation-specific redistribution terms remain unresolved; do not call this table MIT. The supplemental README defines coordinates/side semantics and does not supply a redistribution grant. |
| Blender context assets | See `BLENDER_INTEGRATION_V9_zh.md` and `audit/blender-integration-20261023/source/` | Preserve the supplied source/notice and graph audit. Brain anchors, selected graph and illustrative fly have different evidential roles; none supplies measured neurite geometry or body registration. |

The public research snapshot already contains annotation bytes and generating
source snapshots. This audit does not erase that history or retrospectively
assert permission that has not been established. Before a new public archival
Release, confirm the annotation-specific terms and the transformed-table terms.
Saved-record analysis and plant/input replay do not need the external tables;
fresh neural simulation does. This separates reviewer-accessible evidence from
an installed, licensed, complete experimental environment.

## Exact external input byte provenance

The Parquet exactly matches upstream Git blob
`d386555d1a5f40ebfa1380bcb05b1fab044855fd` at model commit91bdd1e7.
The exercised model.py and completeness CSV differ from upstream only by CRLF
checkout representation (373 and138640 line endings respectively); CRLF-to-LF
comparison reproduces upstream blobs5ba7083c andb5a26b82. Original input bytes
were NOT rewritten. See `audit/v10/upstream-access/model-input-origin-resolved.json`.
An initial exact-byte mismatch report is retained and resolved, not deleted.
`check_model_inputs_v10.py` refuses changed input hashes before neural work and
can check the strict frozen runtime. Source provenance is distinct from a
dataset-specific redistribution grant; the terms caveats above remain.
