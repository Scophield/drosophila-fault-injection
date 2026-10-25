"""Paired 600-ms healthy/deletion sensitivity to the sensory refractory variant."""
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'sim'),str(ROOT/'sim_vision')]


def main():
    import numpy as np
    import brian2
    from brian2 import ms
    from vision_core import VisionSim
    from engine import get_type_ids
    from run_closedloop import build_fault
    from run_provenance import prepare,sha256
    out=ROOT/'runs/refractory-v4'
    os.environ['FLY_RUN_DIR']=str(out)
    params=dict(duration_ms=600,seeds=[12,13,14],sensory_refractory_ms=[2.2,0.],
                faults=[None,'F2_50'],input_hz=150,neural_dt_ms=.1,
                brian_seed_rule='20000+seed',fault_seed_rule='10000+seed',
                scope='conditional three-seed paired model-variant sensitivity, no equivalence claim')
    batch=prepare(out/'paired',params)
    ids=get_type_ids()
    sensory=sorted(ids['LC4']+ids['LPLC2'])
    command=sorted(sum((ids[t] for t in ('DNp01','DNa02','DNp04','DNb01')),[]))
    start=time.perf_counter()
    sim=VisionSim()
    sim.arm_stim_weights(sensory)
    result=dict(complete=False,simulations_executed=True,parameters=params,
                neurons=sim.n_neurons,connections=sim.n_syn,build_seconds=time.perf_counter()-start,
                manifest_sha256=sha256(batch/'run_manifest.json'),trials=[])
    path=batch/'results.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    campaign_start=time.perf_counter()
    for seed in params['seeds']:
        for refractory in params['sensory_refractory_ms']:
            for fault in params['faults']:
                sim.reset_state()
                sim.neu.rfc[[sim.flyid2i[f] for f in sensory]]=refractory*ms
                if fault:
                    sim.apply_weights(build_fault(sim,fault,np.random.default_rng(10000+seed)))
                brian2.seed(20000+seed)
                sim.set_frame_rates([150.]*len(sensory))
                start=time.perf_counter()
                sim.run_frame(600)
                rec=sim.spike_records(command)
                row=dict(seed=seed,sensory_refractory_ms=refractory,fault=fault,
                         command_spikes=len(rec['t_ms']),rate_hz=len(rec['t_ms'])/(8*.6),
                         first_spike_ms=float(min(rec['t_ms'])) if len(rec['t_ms']) else None,
                         network_spikes=int(sim.mon_all.num_spikes),run_seconds=time.perf_counter()-start)
                result['trials'].append(row)
                path.write_text(json.dumps(result,indent=2)+'\n')
                print(json.dumps(row),flush=True)
    result.update(complete=True,wall_seconds=time.perf_counter()-campaign_start)
    path.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__': main()
