# V10.1 public exact-landmark execution protocol

Execute the existing retrospective all-record burst-end analysis over the same 576 records, using B = trigger + 250 ms + 450 ms and H = 1000 ms. Reconstruct exact positions, heading, clearance, contact and phase labels from stored event segments. Preserve all cohort statuses, including earlier contacts, ongoing bursts and zero follow-up.

Export all records, paired differences, status accounting and state-based kinematic calculations with fixed plant constants. Use 10,000 whole-seed descriptive bootstrap draws within RF, RNG 20261025, matching the original computation. Do not fit thresholds or alter original task labels. Synthetic geometric fixtures are software checks, separate from experimental observations.

The state-continuation calculations describe this plant and its observed command-gating regime. They are distinct from the 400-ms scalar-warning evaluation. The distributed historical outputs retain their original source and plan metadata; this document identifies the current public execution instructions.
