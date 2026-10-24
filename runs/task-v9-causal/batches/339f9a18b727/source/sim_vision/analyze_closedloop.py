import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from closedloop_protocol import calibration_keys, episode_key

OUT = Path(__file__).resolve().parent / "results_vision"


def main(tag, input_dir, output_file, calibration=None):
    calibration = calibration or input_dir/'calib.json'
    training = calibration_keys(json.loads(calibration.read_text()), input_dir/'episodes_train')
    rows=[]
    keys=set()
    for path in sorted((input_dir/f'episodes_{tag}').glob('*.json')):
        row=json.loads(path.read_text())
        key=(row['mode'],row['fault'],row['phi_t_deg'],row['seed'])
        if key in keys:
            raise ValueError(f'duplicate episode {key}')
        keys.add(key)
        rows.append(row)
    if not rows:
        raise ValueError('no episodes found')
    agg = defaultdict(list)
    for r in rows:
        split = 'calibration_scenario' if episode_key(r) in training else 'nonoverlap'
        key = (r["mode"], r["fault"] or "healthy", r["phi_t_deg"], split)
        agg[key].append(r)
    print(f"{'mode':<10} {'fault':<10} {'phi':>5} {'esc':>6} {'min_d med':>10} {'spikes med':>11}")
    stats = []
    for key in sorted(agg):
        rs = agg[key]
        esc = sum(1 for r in rs if r["escaped"]) / len(rs)
        md = np.median([r["min_dist"] for r in rs])
        sp = np.median([r["n_total"] for r in rs])
        stats.append({"mode": key[0], "fault": key[1], "phi": key[2], "split":key[3], "n": len(rs), "esc_rate": esc, "min_d_med": md, "spikes_med": sp})
        print(f"{key[0]:<10} {key[1]:<10} {key[2]:>5.0f} {esc:>5.0%} {md:>10.3f} {sp:>11.0f}")
    import csv
    output_file.parent.mkdir(parents=True,exist_ok=True)
    with output_file.open("x", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["mode", "fault", "phi", "split", "n", "esc_rate", "min_d_med", "spikes_med"])
        w.writeheader()
        w.writerows(stats)
    print("\nEscape counts on the four standard azimuths (frontal reported separately):")
    standard=defaultdict(list)
    frontal=defaultdict(list)
    for row in rows:
        split = 'calibration_scenario' if episode_key(row) in training else 'nonoverlap'
        key=(row['mode'],row['fault'] or 'healthy',split)
        (frontal if row['phi_t_deg']==0 else standard)[key].append(row)
    for label,groups in [('standard',standard),('frontal',frontal)]:
        for key,group in sorted(groups.items()):
            print(f"  {label} {key}: {sum(r['escaped'] for r in group)}/{len(group)}")



if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="v4")
    ap.add_argument('--input',type=Path,default=OUT)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--calibration',type=Path)
    args=ap.parse_args()
    main(args.tag,args.input,args.out,args.calibration)
