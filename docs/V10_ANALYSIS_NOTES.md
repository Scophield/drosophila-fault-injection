# Analysis implementation and hierarchy clarifications

The frozen V9/V10 registration JSONs list **loss/gain and exposure** as primary.
Net loss is their algebraic difference, **derived**, while the between-law
net-loss interaction and warnings are prespecified secondary. V10 prose and
tables must not promote the latter or call a prespecified secondary endpoint
exploratory. The main plot now uses the primary healthy-to-fault loss; derived
net loss and the interaction keep their distinct labels. Loss/gain displays are
percent of paired scenarios; signed net-loss/interaction displays are percentage
points. Stored numerical estimates remain unscaled proportions with an explicit
display scale, not mislabeled percentage values.

All reported percentile intervals are pointwise and conditional on the stored
RF realization, development fit and frozen validation thresholds. They do not
resample calibration datasets or provide simultaneous coverage across every
map/law/dose/metric. The declared four-test Holm correction concerns the new
secondary interaction sensitivity family, not all displayed confidence intervals.

These labels were tightened after rechecking the frozen JSON during ongoing
testing, before inspecting test outcomes. Registrations, numerical estimands,
seeds, source snapshots and raw records were NOT edited. The first analysis-code
checkpoint remains preserved; a second checkpoint records the metadata correction.
Checkpoint03 adds a pre-analysis RF-to-input-map binding guard only; it changes
no numerical estimand. All checkpoints precede inspection of test outcomes and
are post-launch engineering records, not externally timestamped preregistrations.
The registered analyzer and neural runner remain unchanged throughout the campaign.

The zero-event safeguard was added after registration as an uncertainty reporting
diagnostic. A degenerate bootstrap interval does not establish zero risk. When
all observed loss/gain clusters are zero at one law/dose, the one-sided95% upper
bound `1 - 0.05**(1/n)` concerns ANY such event across the two bearings in a new
identically defined cluster. It is not a conditional FNR, a two-sided net-loss
interval or a simultaneous guarantee across maps/conditions. It is not presented
as a new primary metric or a preregistered protection rule.

RF input rows must be in canonical numeric FlyID order because the inherited
stimulation interface sorts those identities. The supplied generator already
produces this order; preflight now explicitly rejects an unsorted custom map.
The frozen runner is not changed mid-campaign. Both complete32-record validation
sets independently replay their actual input-event digests and geometry, confirming
the new maps are used consistently. This is trace/input consistency, not neural
execution attestation. A custom map requires a new design/output directory.
