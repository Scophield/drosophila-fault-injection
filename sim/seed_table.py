import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

OPEN = [
    "healthy",
    "F1_wvar_05", "F1_wvar_10", "F1_wvar_20", "F1_wvar_50",
    "F2_drop_05", "F2_drop_10", "F2_drop_25", "F2_drop_50",
    "F3_loss_01", "F3_loss_02", "F3_loss_05", "F3_loss_10",
    "F4_hub_1pct", "F4_hub_2pct", "F4_hub_5pct",
    "F5_in_LC4", "F5_in_LPLC2", "F5_in_both",
]

CTRL = [
    "healthy_d75", "healthy_d150", "healthy_d300",
    "F2_50_d75", "F2_50_d150", "F2_50_d300",
    "F4_1pct_d75", "F4_1pct_d150", "F4_1pct_d300",
    "EIm_1pct", "EIm_2pct",
    "HUB_inh", "HUB_exc",
    "INHrand_cells", "INHrand_mass",
]

N_TRIALS = 12


def seed_sha(key):
    return int(hashlib.sha256(key.encode()).hexdigest()[:16], 16)


def main():
    out = {
        "open_loop": {
            "derivation": "int(sha256('<phase>|<condition>|<trial>')[:16], 16)",
            "phase": "real",
            "trials": N_TRIALS,
            "seeds": {
                c: [seed_sha(f"real|{c}|{k}") for k in range(N_TRIALS)] for c in OPEN
            },
        },
        "controls": {
            "derivation": "int(sha256('ctrl|<condition>|<trial>')[:16], 16)",
            "phase": "ctrl",
            "trials": N_TRIALS,
            "seeds": {
                c: [seed_sha(f"ctrl|{c}|{k}") for k in range(N_TRIALS)] for c in CTRL
            },
        },
        "closed_loop": {
            "derivation": "brian2.seed(20000+seed); numpy default_rng(10000+seed)",
            "seeds": [0, 1, 2],
            "azimuths_deg": [-60, -30, 30, 60],
        },
    }
    (ROOT / "seeds.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote seeds.json: {len(OPEN)} open-loop, {len(CTRL)} control conditions")


if __name__ == "__main__":
    main()
