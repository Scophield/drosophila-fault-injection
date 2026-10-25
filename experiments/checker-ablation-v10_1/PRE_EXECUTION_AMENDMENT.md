# Pre-execution amendment: worker partition control

This amendment was made before final challenge scoring. Structural review of
version 1 showed that `legal_worker_seed_partition` selected an already declared
single-seed block without changing the evaluated collection. That was a valid
record control, but did not directly exercise coexistence of genuine worker
manifests. No observed detection score motivated this amendment.

The original plan is preserved byte-for-byte as `challenge-spec-v1.json`, SHA256
`fc6d6b6ae631356d32ac2ee0b5755c35b12a56a074cdd12a6b9bda0cdae1624a`.
`challenge-spec.json` is the active version 2 plan.

Only the worker-control family changes:

- Preserve the source group selected by the original seeded shuffle and the
  original target-row RNG draw. Additional source selection consumes no RNG,
  so every other family's source groups and target draws remain unchanged.
- For fly, append the lowest-seed eligible block from the same adapter/RF whose
  real `run_manifest_sha256` set is nonempty and disjoint from the first block.
  Retain both complete matrices, all raw rows and their worker metadata. Declare
  both seed clusters in the case's subcampaign. This evaluates 24 rows drawn from
  two true workers, without inventing a worker or altering any source hash.
- For tank, append the lowest other seed in the same adapter. Tank records have
  no worker manifest, so this tests only a legitimate declared two-seed
  subcampaign; it is not evidence of actual worker partition support.
- If an eligible second source block is unavailable, retain the case with an
  explicit inapplicability reason rather than replacing it or excluding it
  silently.

There remain 111 planned cases: 57 fly and 54 tank. Each applicable worker-control
case has 24 rows; other cases retain their original 12-row source blocks. Ground
truth, all other families, perturbation parameters and the fixed checker remain
unchanged. This remains an author-designed fixed additional evaluation, not a
blind or population-level generalization study.
