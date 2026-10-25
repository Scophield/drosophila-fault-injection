# Fixed additional four-arm checker evaluation

The frozen catalogue has 111 designed case IDs (87 known corruptions and 24 valid controls), 107 unique applicable raw/spec inputs. All 444 primary and 72 technical execution rows are complete. Six preselected source cases have three extra technical runs per arm; these runs do not add efficacy samples.

A is the trusted header-registry baseline; B adds the complete Common audit; C adds native record/pair replay; D combines all obligations. This is an author-designed fixed additional evaluation, not blind generalization or a comparison with unexecuted external tools.

## Designed case counts

| Plant | Arm | Invalid | Valid | Detected invalid | Missed invalid | False alarms | Accepted valid |
|---|---|---|---|---|---|---|---|
| fly | A | 45 | 12 | 18 | 27 | 0 | 12 |
| fly | B | 45 | 12 | 27 | 18 | 0 | 12 |
| fly | C | 45 | 12 | 39 | 6 | 0 | 12 |
| fly | D | 45 | 12 | 39 | 6 | 0 | 12 |
| tank | A | 42 | 12 | 18 | 24 | 0 | 12 |
| tank | B | 42 | 12 | 27 | 15 | 0 | 12 |
| tank | C | 42 | 12 | 36 | 6 | 0 | 12 |
| tank | D | 42 | 12 | 42 | 0 | 0 | 12 |
| all | A | 87 | 24 | 36 | 51 | 0 | 24 |
| all | B | 87 | 24 | 54 | 33 | 0 | 24 |
| all | C | 87 | 24 | 75 | 12 | 0 | 24 |
| all | D | 87 | 24 | 81 | 6 | 0 | 24 |

## Unique raw/spec input counts

| Plant | Arm | Invalid | Valid | Detected invalid | Missed invalid | False alarms | Accepted valid |
|---|---|---|---|---|---|---|---|
| fly | A | 45 | 11 | 18 | 27 | 0 | 11 |
| fly | B | 45 | 11 | 27 | 18 | 0 | 11 |
| fly | C | 45 | 11 | 39 | 6 | 0 | 11 |
| fly | D | 45 | 11 | 39 | 6 | 0 | 11 |
| tank | A | 42 | 9 | 18 | 24 | 0 | 9 |
| tank | B | 42 | 9 | 27 | 15 | 0 | 9 |
| tank | C | 42 | 9 | 36 | 6 | 0 | 9 |
| tank | D | 42 | 9 | 42 | 0 | 0 | 9 |
| all | A | 87 | 20 | 36 | 51 | 0 | 20 |
| all | B | 87 | 20 | 54 | 33 | 0 | 20 |
| all | C | 87 | 20 | 75 | 12 | 0 | 20 |
| all | D | 87 | 20 | 81 | 6 | 0 | 20 |

## Nonredundant information above A

| Plant | Unit | B−A | C−A | D−A | B-only | C-only | B/C overlap above A | Full misses |
|---|---|---|---|---|---|---|---|---|
| fly | designed_cases | 9 | 21 | 21 | 0 | 12 | 9 | 6 |
| fly | unique_inputs | 9 | 21 | 21 | 0 | 12 | 9 | 6 |
| tank | designed_cases | 9 | 18 | 24 | 6 | 15 | 3 | 0 |
| tank | unique_inputs | 9 | 18 | 24 | 6 | 15 | 3 | 0 |
| all | designed_cases | 18 | 39 | 45 | 6 | 27 | 12 | 6 |
| all | unique_inputs | 18 | 39 | 45 | 6 | 27 | 12 | 6 |

Counts describe this fixed catalogue only. B/C overlap includes neither duplicate input IDs nor baseline findings when labelled “above A.” The measured Full decision equals B-or-C for every completed execution.

## Primary costs

| Plant | Arm | Cases | Wall total (s) | Wall median (s) | CPU total (s) | CPU median (s) | Sampled RSS max (MiB) |
|---|---|---|---|---|---|---|---|
| fly | A | 57 | 0.1163 | 0.0016 | 0.0312 | 0.0000 | 237.8 |
| fly | B | 57 | 0.3388 | 0.0048 | 0.2188 | 0.0000 | 238.4 |
| fly | C | 57 | 74.0444 | 1.2927 | 73.0156 | 1.2656 | 445.6 |
| fly | D | 57 | 75.3276 | 1.3076 | 73.4375 | 1.2812 | 445.8 |
| tank | A | 54 | 0.1049 | 0.0013 | 0.0312 | 0.0000 | 273.8 |
| tank | B | 54 | 0.3100 | 0.0048 | 0.2500 | 0.0000 | 273.8 |
| tank | C | 54 | 0.7552 | 0.0119 | 0.6406 | 0.0156 | 273.8 |
| tank | D | 54 | 0.9351 | 0.0154 | 0.8594 | 0.0156 | 273.8 |
| all | A | 111 | 0.2212 | 0.0015 | 0.0625 | 0.0000 | 273.8 |
| all | B | 111 | 0.6488 | 0.0048 | 0.4688 | 0.0000 | 273.8 |
| all | C | 111 | 74.7996 | 0.2265 | 73.6562 | 0.2188 | 445.6 |
| all | D | 111 | 76.2627 | 0.2304 | 74.2969 | 0.2188 | 445.8 |

### Valid controls only

| Plant | Arm | Valid cases | Wall median (s) | CPU total (s) | Starting RSS median (MiB) | Sampled RSS max (MiB) |
|---|---|---|---|---|---|---|
| fly | A | 12 | 0.0017 | 0.0156 | 236.8 | 237.2 |
| fly | B | 12 | 0.0066 | 0.1094 | 236.9 | 237.9 |
| fly | C | 12 | 1.3289 | 19.2031 | 237.3 | 443.4 |
| fly | D | 12 | 1.3219 | 19.4219 | 236.9 | 445.1 |
| tank | A | 12 | 0.0018 | 0.0312 | 273.4 | 273.7 |
| tank | B | 12 | 0.0062 | 0.0781 | 273.4 | 273.7 |
| tank | C | 12 | 0.0132 | 0.1719 | 273.4 | 273.7 |
| tank | D | 12 | 0.0168 | 0.2031 | 273.1 | 273.7 |
| all | A | 24 | 0.0017 | 0.0469 | 255.1 | 273.7 |
| all | B | 24 | 0.0065 | 0.1875 | 255.5 | 273.7 |
| all | C | 24 | 0.6423 | 19.3750 | 255.5 | 443.4 |
| all | D | 24 | 0.6618 | 19.6250 | 255.5 | 445.1 |

Frozen-plan initialization/registry: 2.0677 s; complete preparation: 10.8169 s; run initialization: 2.2353 s. These are separate from per-case costs. RSS is 5-ms sampled absolute process memory, including retained fixtures, not per-case allocation or an independent worker peak. Short peaks may be missed; coarse CPU clock resolution can yield zero for fast checks. Paired cost differences and three-run technical ranges are in summary.json and technical-repeats.csv; they are not confidence intervals.

## Family-level decisions

| Plant | Family | Invalid/valid | A TP/FN/FP | B TP/FN/FP | C TP/FN/FP | D TP/FN/FP |
|---|---|---|---|---|---|---|
| fly | unaltered | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| fly | legal_nonframe_actuation | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| fly | legal_worker_seed_partition | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| fly | legal_feedback_dependence | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| fly | uniform_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | mask_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | seed_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | condition_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | actuator_start | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| fly | actuator_end | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| fly | endpoint_actuator_state | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| fly | task_label_contradiction | 3/0 | 0/3/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | first_failure_time | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| fly | resource_decrease | 3/0 | 0/3/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | monotone_resource_bias | 3/0 | 0/3/0 | 0/3/0 | 0/3/0 | 0/3/0 |
| fly | truncated_exposure | 3/0 | 0/3/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | missing_required_header | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | uniform_binding_replacement | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| fly | declared_burst_header | 3/0 | 0/3/0 | 0/3/0 | 0/3/0 | 0/3/0 |
| tank | unaltered | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| tank | legal_nonframe_actuation | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| tank | legal_worker_seed_partition | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| tank | legal_feedback_dependence | 0/3 | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| tank | uniform_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| tank | mask_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| tank | seed_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| tank | condition_identity | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| tank | actuator_start | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| tank | actuator_end | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| tank | endpoint_actuator_state | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| tank | task_label_contradiction | 3/0 | 0/3/0 | 3/0/0 | 0/3/0 | 3/0/0 |
| tank | first_failure_time | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| tank | resource_decrease | 3/0 | 0/3/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| tank | monotone_resource_bias | 3/0 | 0/3/0 | 0/3/0 | 3/0/0 | 3/0/0 |
| tank | truncated_exposure | 3/0 | 0/3/0 | 3/0/0 | 0/3/0 | 3/0/0 |
| tank | missing_required_header | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |
| tank | uniform_binding_replacement | 3/0 | 3/0/0 | 3/0/0 | 3/0/0 | 3/0/0 |

Full misses: 6. All primary false alarms across arms: 0. Every arm-specific miss/false alarm and its mutation/source context is retained in all-misses.csv / all-false-positives.csv, not removed from the denominator.

| Full-missed case | Plant | Family |
|---|---|---|
| fly:monotone_resource_bias:01 | fly | monotone_resource_bias |
| fly:monotone_resource_bias:02 | fly | monotone_resource_bias |
| fly:monotone_resource_bias:03 | fly | monotone_resource_bias |
| fly:declared_burst_header:01 | fly | declared_burst_header |
| fly:declared_burst_header:02 | fly | declared_burst_header |
| fly:declared_burst_header:03 | fly | declared_burst_header |

Validity is a frozen source-corruption oracle, not a label chosen from checker output. The trusted registry is a prerequisite; consistent unlogged neural fabrication remains outside trace authentication. Original development challenges, genuine V8 errors, and these additional fixtures are separate evidence sets. No new neural simulation, population claim, or hypothetical collision effect is inferred here.
