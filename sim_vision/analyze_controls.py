import json
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "results_vision" / "openloop_controls"
BASE = Path(__file__).resolve().parent / "results_vision"
N_BOOT = 20000


def boot_ci(x, f=np.median, n=N_BOOT, seed=0):
    x = np.asarray(x, dtype=np.float64)
    if len(x) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n, len(x)))
    vals = np.array([f(x[i]) for i in idx[::1]])
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def load(path):
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return rows


def summarize(rows):
    rate = np.array([r["pop_rate"] for r in rows])
    tot = np.array([r["n_total_spikes"] for r in rows])
    lat = np.array([r["latency_ms"] for r in rows if r["latency_ms"] is not None])
    return {
        "n": len(rows),
        "rate_med": float(np.median(rate)),
        "rate_ci": boot_ci(rate),
        "rate_min": float(rate.min()),
        "rate_max": float(rate.max()),
        "tot_med": float(np.median(tot)),
        "tot_ci": boot_ci(tot),
        "lat_med": float(np.median(lat)) if len(lat) else None,
        "pass_frac": float(np.mean(rate >= 51.4)),
    }


def main():
    files = sorted(OUT.glob("*.jsonl"))
    res = {}
    for f in files:
        res[f.stem] = summarize(load(f))
    (OUT / "summary.json").write_text(json.dumps(res, indent=2))

    hdr = f"{'condition':<16}{'n':>4}{'rate':>8}{'95% CI':>18}{'spikes':>10}{'lat':>7}{'pass':>7}"
    print(hdr)
    for k, v in res.items():
        ci = f"[{v['rate_ci'][0]:.1f},{v['rate_ci'][1]:.1f}]"
        lat = f"{v['lat_med']:.2f}" if v["lat_med"] else "-"
        print(f"{k:<16}{v['n']:>4}{v['rate_med']:>8.1f}{ci:>18}{v['tot_med']:>10.0f}{lat:>7}{v['pass_frac']:>7.2f}")

    try:
        old = {}
        for name in ("healthy", "F2_drop_50", "F4_hub_1pct"):
            p = BASE / "real" / f"{name}.jsonl"
            if p.exists():
                old[name] = summarize(load(p))
        if old:
            print("\nreference (sim/results/real):")
            for k, v in old.items():
                print(f"  {k:<14}{v['rate_med']:>7.1f}  [{v['rate_ci'][0]:.1f},{v['rate_ci'][1]:.1f}]  "
                      f"spikes {v['tot_med']:.0f}")
            (OUT / "summary_reference.json").write_text(json.dumps(old, indent=2))
    except Exception as exc:
        print("reference summary failed:", exc)


if __name__ == "__main__":
    main()
