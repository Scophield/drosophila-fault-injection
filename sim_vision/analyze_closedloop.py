import json
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "results_vision"


def main(tag="main"):
    import glob
    rows = []
    for f in sorted(glob.glob(str(OUT / f"closedloop_{tag}_*.jsonl"))):
        if "closedloop_%s_" % tag in f:
            rows.extend(json.loads(l) for l in open(f))
    agg = defaultdict(list)
    for r in rows:
        key = (r["mode"], r["fault"] or "healthy", r["phi_t_deg"])
        agg[key].append(r)
    print(f"{'mode':<10} {'fault':<10} {'phi':>5} {'esc':>6} {'min_d med':>10} {'spikes med':>11}")
    stats = []
    for key in sorted(agg):
        rs = agg[key]
        esc = sum(1 for r in rs if r["escaped"]) / len(rs)
        md = np.median([r["min_dist"] for r in rs])
        sp = np.median([r["n_total"] for r in rs])
        stats.append({"mode": key[0], "fault": key[1], "phi": key[2], "n": len(rs), "esc_rate": esc, "min_d_med": md, "spikes_med": sp})
        print(f"{key[0]:<10} {key[1]:<10} {key[2]:>5.0f} {esc:>5.0%} {md:>10.3f} {sp:>11.0f}")
    import csv
    with (OUT / f"closedloop_{tag}_summary.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["mode", "fault", "phi", "n", "esc_rate", "min_d_med", "spikes_med"])
        w.writeheader()
        w.writerows(stats)
    by_mode = defaultdict(list)
    for s in stats:
        by_mode[(s["mode"], s["fault"])].append(s["esc_rate"])
    print("\nEscape rate by mode/fault (mean over azimuths):")
    for k in sorted(by_mode):
        print(f"  {k[0]:<10} {k[1]:<10} {np.mean(by_mode[k]):>5.0%}")


if __name__ == "__main__":
    main()
