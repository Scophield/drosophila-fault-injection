import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "sim/results/real"
CTRL = ROOT / "sim_vision/results_vision/openloop_controls"
THETA = 51.4
ENV = 2.0


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def med(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def main():
    base = load(CORE / "healthy.jsonl")
    b_rate = med([r["pop_rate"] for r in base])
    b_tot = med([r["n_total_spikes"] for r in base])
    conds = {}
    for p in sorted(CORE.glob("*.jsonl")):
        if p.stem != "healthy":
            conds[p.stem] = p
    for p in sorted(CTRL.glob("*.jsonl")):
        if p.stem.startswith(("HUB_", "EIm_", "INHrand_")):
            conds[p.stem] = p

    tot = acc_ok = env_ok = 0
    rows = []
    for name, p in conds.items():
        rs = load(p)
        a = e = 0
        for r in rs:
            rate, tot_sp = r["pop_rate"], r["n_total_spikes"]
            acc = rate >= THETA
            env = acc and rate <= ENV * b_rate and tot_sp <= ENV * b_tot
            a += acc
            e += env
        rows.append((name, len(rs), a, e))
        tot += len(rs)
        acc_ok += a
        env_ok += e

    print(f"baseline {b_rate:.1f} Hz  {b_tot:.0f} spikes  theta {THETA}  envelope {ENV:.0f}x")
    print(f"{'condition':16s} {'n':>3s} {'transmit':>9s} {'envelope':>9s}")
    for name, n, a, e in rows:
        print(f"{name:16s} {n:3d} {a:3d}/{n:<3d}   {e:3d}/{n:<3d}")
    print(f"{'all':16s} {tot:3d} {acc_ok:3d}/{tot:<3d}   {env_ok:3d}/{tot:<3d}")
    print(f"accuracy-only pass {100 * acc_ok / tot:.1f}%  dual {100 * env_ok / tot:.1f}%")

    out = {
        "baseline_rate_hz": b_rate,
        "baseline_spikes": b_tot,
        "theta_hz": THETA,
        "envelope": ENV,
        "trials": tot,
        "accuracy_only_pass": acc_ok,
        "envelope_pass": env_ok,
        "conditions": [
            {"name": n, "trials": c, "transmission": a, "envelope": e}
            for n, c, a, e in rows
        ],
    }
    (ROOT / "sim/results/protocol_scores.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
