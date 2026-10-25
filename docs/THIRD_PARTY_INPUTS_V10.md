# External inputs and attribution

Saved-record analysis, timing tables, evidence checks and paper compilation use the distributed files. Fresh neural simulation uses pinned external model inputs.

| Input | Source and identity | Access and attribution |
|---|---|---|
| Model code | philshiu/Drosophila_brain_model, commit 91bdd1e7dcf193f3e7ca5a8933497fcef63b7960 | MIT notices are preserved in THIRD_PARTY_LICENSES/model-MIT.txt and generating snapshots. |
| Completeness_783.csv and Connectivity_783.parquet | Same pinned model release; exact input hashes are in the frozen registrations and PUBLIC_SCOPE.json | Obtain the original tables from the upstream model/deposit and match their hashes before new neural runs. The publication distributes generated configurations and records separately from these tables. |
| FlyWire v783 connectivity | https://doi.org/10.5281/zenodo.10676866 | Attribute the original FlyWire reconstruction and synapse/annotation works; the underlying deposit specifies CC-BY-4.0. |
| Annotation input | https://github.com/flyconnectome/flywire_annotations/blob/a83b2776d60d5764cef36b927f5f9679c16c47a2/supplemental_files/Supplemental_file1_neuron_annotations.tsv | Use the pinned upstream source under its applicable terms; its byte hash is recorded in PUBLIC_SCOPE.json. The table is acquired separately. |
| Approved figure assets | paper/figs/ | The compiled paper uses the supplied rendered/vector PDFs. Private Blender engineering files and system TTF files are separate from this scientific distribution. |

Project MIT licensing applies to project code; preserve upstream notices and applicable dataset terms when obtaining external inputs. Exact generation-time configurations, input identifiers and observations remain in runs/.
