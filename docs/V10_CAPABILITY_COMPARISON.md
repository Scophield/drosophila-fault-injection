# Incremental capability and measured scope

This comparison uses documented positive capabilities, not inferred absences.
SpikeFI, SpikingJET, enpheeph, Breach and Loihi2 were not executed as comparators.
No overhead, accuracy, coverage or fault-tolerance superiority is claimed over them.

| Established work | Primary-source capability inspected | V10's tested scope |
|---|---|---|
| [SpikeFI](https://arxiv.org/abs/2412.06795) | Configurable neuron/synapse faults and automated SNN campaigns | Check complete paired record matrices, declared shared randomness and native task clocks after generation |
| [SpikingJET](https://arxiv.org/abs/2404.00383) | Faults in weights, neuron parameters, states and activation functions | Independent replay of the declared plant/input/actuator semantics; no new physical fault model |
| [enpheeph](https://arxiv.org/abs/2208.00328) | Configurable SNN/compressed-network fault injection, specialized-device execution | Two native record adapters use one common checker; this is adoption evidence, not an injector runtime comparison |
| [Glasserman & Yao](https://doi.org/10.1287/mnsc.38.6.884) | CRN synchronization and conditions for its benefit | Verify indexed variates and nested masks from records; no new CRN algorithm or universal variance-reduction claim |
| [Breach](https://doi.org/10.1007/978-3-642-14295-6_17) | Temporal monitoring of simulated hybrid trajectories | Pair/source/exposure invariants plus adapter replay for fault campaigns; no new temporal-logic or falsification algorithm |
| [NeuroBench](https://doi.org/10.1038/s41467-025-56739-4) | Functional/resource benchmarking framework | Explicit own-stop/common/fixed exposure and task labels within this artifact; no hardware cost inference |
| [D'Angelo et al.2026](https://doi.org/10.1038/s42256-026-01197-w) | A task/metric framework with a reproducible physical soft-robot platform, confirmed in the primary abstract/code-availability statement | Paired fault-campaign consistency and native input/actuator replay on saved records; no claim to invent embodied benchmarking or outperform the physical platform |

Positive evidence is concrete: the final same checker accepts 288 baseline neural
and 96 tank records;14 selected corruption types per adapter are detected. Five
real-manifest regressions check source/calibration integrity, and declaration
guards reject empty/duplicate campaigns. The standalone tank example was actually
run in a new minimal dependency environment without fly/Brian2 imports. Its
repeat adds no independent samples. Both independent RF matrices tested the same
interface after they are complete, without changing registered analysis roles.

A deliberately synthetic zero-readout logger passes the trace check without
executing neural equations. Thus the interface is not execution attestation,
solver verification, physical-model validation, a safety certificate or exhaustive
fault coverage. Hand-written native replayers share assumptions with generators.
The contribution is a bounded engineering interface with executable evidence;
whether that advance is sufficient for a regular ISCAS paper remains a review risk.
