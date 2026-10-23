import numpy as np
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'sim'))
from project_paths import PATH_COMP, PATH_ANN

SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parent

RF_SEED = 20260201
SIGMA_RF_DEG = 30.0
GRAD_GAIN = 0.8
R_MAX = 150.0
FRAME_DT_MS = 20.0


def load_sensory():
    ann = pd.read_csv(PATH_ANN, sep="\t", low_memory=False)
    comp = pd.read_csv(PATH_COMP, index_col=0)
    comp_ids = set(comp.index.astype("int64"))
    a = ann[ann.root_id.isin(comp_ids)]
    rows = []
    for t in ["LC4", "LPLC2"]:
        sub = a[a.cell_type == t][["root_id", "side", "pos_z"]]
        for _, r in sub.iterrows():
            rows.append({"root_id": int(r.root_id), "cell_type": t, "side": r.side, "pos_z": float(r.pos_z)})
    df = pd.DataFrame(rows).sort_values("root_id").reset_index(drop=True)
    return df


def build_rf_map(df, seed=RF_SEED):
    rng = np.random.default_rng(seed)
    z = df["pos_z"].to_numpy(dtype=float)
    z_norm = (z - z.min()) / max(z.max() - z.min(), 1e-9)
    phi = np.where(
        df["side"].to_numpy() == "left",
        rng.uniform(10.0, 90.0, len(df)),
        rng.uniform(-90.0, -10.0, len(df)),
    )
    psi = -30.0 + 90.0 * z_norm
    w_grad = np.where(
        df["cell_type"].to_numpy() == "LPLC2",
        1.0 + GRAD_GAIN * (psi - (-30.0)) / 90.0,
        1.0,
    )
    rf = pd.DataFrame({"root_id": df.root_id, "cell_type": df.cell_type, "side": df.side, "phi_deg": phi, "psi_deg": psi, "w_grad": w_grad})
    return rf


def loom_trajectory(radius_m, v_m, dur_ms, t_start_ms, frame_dt_ms=FRAME_DT_MS, d0_m=0.25):
    n = int(round(dur_ms / frame_dt_ms)) + 1
    ts = np.arange(n) * frame_dt_ms / 1000.0
    dist = np.maximum(d0_m - v_m * (ts - t_start_ms / 1000.0), 0.02)
    half_angle = np.degrees(np.arctan(radius_m / dist))
    da_dt = np.gradient(half_angle, frame_dt_ms / 1000.0)
    u = np.clip(da_dt / 150.0, 0.0, None) * np.exp(-half_angle / 60.0)
    u_max = np.clip(np.degrees(np.arctan(radius_m / 0.02)) / 150.0, 0.0, None) * np.exp(-5.0 / 60.0)
    u = u / max(u_max, 1e-9)
    u[ts < t_start_ms / 1000.0] = 0.0
    return {"t_ms": ts * 1000.0, "dist_m": dist, "half_angle_deg": half_angle, "u": np.minimum(u, 1.0)}


def encode_rates(rf, traj, phi_t_deg, psi_t_deg, frame_dt_ms=FRAME_DT_MS):
    dphi = np.radians(rf["phi_deg"].to_numpy() - phi_t_deg)
    dpsi = np.radians(rf["psi_deg"].to_numpy() - psi_t_deg)
    d2 = dphi**2 + dpsi**2
    sig = np.radians(np.maximum(SIGMA_RF_DEG, np.asarray(traj["half_angle_deg"])))
    gauss = np.exp(-d2[None, :] / (2.0 * sig[:, None] ** 2))
    w = rf["w_grad"].to_numpy()
    rates = np.minimum(R_MAX * w * gauss * traj["u"][:, None], R_MAX)
    return rates


def encode_none(rf, dur_ms, frame_dt_ms=FRAME_DT_MS):
    n = int(round(dur_ms / frame_dt_ms)) + 1
    return np.zeros((n, len(rf)))
