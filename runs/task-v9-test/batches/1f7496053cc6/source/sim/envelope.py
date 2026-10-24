import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
THETA = 51.4

s = json.loads((ROOT / "results" / "summary.json").read_text())["real"]
h = s["healthy"]
rt2, tt2 = h["rate_med"] * 2, h["tot_med"] * 2
print(f"envelope: rate in [{h['rate_med']/2:.1f}, {rt2:.1f}] Hz, total spikes in [{h['tot_med']/2:.0f}, {tt2:.0f}]")
print(f"{'condition':16s} transmission envelope")
for cond, v in s.items():
    recs = [json.loads(l) for l in open(ROOT / "results" / "real" / f"{cond}.jsonl")]
    trans = sum(r["pop_rate"] >= THETA for r in recs)
    env = sum(h["rate_med"] / 2 <= r["pop_rate"] <= rt2 and h["tot_med"] / 2 <= r["n_total_spikes"] <= tt2 for r in recs)
    print(f"{cond:16s} {trans:>4d}/12      {env:>3d}/12")
