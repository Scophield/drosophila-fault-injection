"""Test task feasibility using a privileged geometric rule, without a neural model."""
import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'sim'),str(ROOT/'sim_vision')]
from run_closedloop import run_episode


class NoNeuralModel:
    def __init__(self):
        self.flyid2i={i:i for i in range(8)}
        self.mon_all=SimpleNamespace(num_spikes=0)
    def reset_state(self):
        self.mon_all.num_spikes=0
    def set_frame_rates(self, rates):
        pass
    def run_frame(self, dt):
        pass
    def spike_records(self, ids):
        return dict(t_ms=np.array([],dtype=float),i=np.array([],dtype=int))


def reference(phi, horizon):
    cmd=pd.DataFrame([dict(flyid=i,cell_type=t,side=s) for i,(t,s) in enumerate(
        (t,s) for t in ['DNp01','DNa02','DNp04','DNb01'] for s in ['left','right'])])
    rf=dict(phi_deg=np.array([0.]),psi_deg=np.array([0.]),w_grad=np.ones(1))
    # Positive placeholders satisfy the common runner's API; the rule never reads them.
    calibration=dict(protocol_version='geometry-v2',theta_demo_hz=1.,lr_ref=1.,bias=0.,data_sign=1.)
    row=run_episode(NoNeuralModel(),rf,cmd,0,phi,mode='geometry_rule',
                    calibration=calibration,duration_ms=horizon)
    row.update(neural_simulation=False,deterministic=True,
               interpretation='privileged geometry and onset-triggered burst; task-feasibility reference, not matched neural fault tolerance')
    return row


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    rows=[reference(phi,horizon) for horizon in (800,1000,1200) for phi in (-30.,30.)]
    args.out.mkdir(parents=True,exist_ok=False)
    (args.out/'reference.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps([{k:r[k] for k in ['phi_t_deg','horizon_ms','escaped','min_dist']} for r in rows],indent=2))


if __name__=='__main__':
    main()
