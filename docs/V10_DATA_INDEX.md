# V10.1 canonical data products

The distributed cohorts and derived tables connect each result to its registered inputs and independent seed clusters.

| Product | Source | Unit and role |
|---|---|---|
| RF-0 core | runs/task-v9-test/episodes/; runs/task-v9-frozen/registration-core.json | 24 seed clusters, 288 paired episodes |
| Angle-transfer cohort | runs/task-v9-stress/episodes/ | 8 separate clusters, 96 episodes on RF-0 |
| Action diagnostic cohort | runs/task-v9-causal/episodes/ | 8 separate clusters, 64 episodes under its own registration |
| RF-A/B design | runs/task-v10-design/ | Independent azimuth draws from the shared prior |
| Feasibility records | runs/task-v10-map-A-pilot/; runs/task-v10-map-B-pilot/ | One passive episode per map, separate from development and test |
| RF-A/B development | runs/task-v10-transfer/map-{A,B}/development/episodes/ | 4 development seeds and 20 passive episodes per map |
| RF-A/B validation | runs/task-v10-transfer/map-{A,B}/validation/episodes/ | 8 separate seeds and 32 healthy episodes per map |
| RF-A/B tests | runs/task-v10-transfer/map-{A,B}/test/episodes/ | 12 new seed clusters and 144 episodes per map |
| Delayed-tank adapter | audit/v10/evidence-05/tank-raw/ | 8 tank seed clusters and 96 examples |
| Labelled checker challenges | audit/v10/evidence-05/check.json | 14 predefined challenge types per adapter |
| Native timing examples | audit/v10/legacy-timing-01/check.json | 72 historical records with their own protocol identity |
| All-record action timing | output/trigger-timing-20261025-03/ | 576 records, 384 healthy/fault pairs, 288 P/R pairs |
| Exact burst-end states | output/burst-end-20261025-01/ | All 576 records and explicit landmark/phase accounting |
| State reconstruction checks | output/burst-end-validation-20261025-03/ | Prefix, timing, gate and geometry checks |

The RF summaries and input/plant replays are in audit/acceptance-v9/core-v2/ and audit/v10/transfer-01/. Inference uses whole seed clusters within each RF, with both bearings retained inside a cluster. Development, validation, core, transfer and separate action/angle cohorts retain their distinct roles. The four transfer interactions use their registered Holm family. New timing tables are retrospective descriptive products of the frozen core trajectories.
