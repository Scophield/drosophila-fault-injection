"""Run a bounded full-connectome input/provenance check using real Brian2."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'sim'), str(ROOT / 'sim_vision')]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--backend', choices=['numpy', 'cython'], default='numpy')
    ap.add_argument('--duration-ms', type=float, default=400)
    ap.add_argument('--seeds', default='0,1,2')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    from run_provenance import sha256, code_hash
    from project_paths import MODEL_DIR, PATH_CON, PATH_COMP, PATH_ANN
    summary = dict(status='started', backend=args.backend, duration_ms=args.duration_ms,
                   python=sys.version, processor=platform.processor(),
                   packages={p:importlib.metadata.version(p) for p in
                             ['brian2','numpy','pandas','pyarrow','Cython','joblib']},
                   code_sha256=code_hash(), inputs={str(p):sha256(p) for p in
                             [MODEL_DIR/'model.py', PATH_CON, PATH_COMP, PATH_ANN]},
                   simulations_executed=False, trials=[])
    path = args.out / 'validation.json'
    path.write_text(json.dumps(summary, indent=2)+'\n')
    try:
        from vision_core import VisionSim
        from engine import get_type_ids
        import brian2
        from brian2 import prefs, ms
        prefs.codegen.target = args.backend
        start = time.perf_counter()
        sim = VisionSim()
        ids = get_type_ids()
        sensory = sorted(ids['LC4'] + ids['LPLC2'])
        command = sorted(sum((ids[t] for t in ['DNp01','DNa02','DNp04','DNb01']), []))
        sim.arm_stim_weights(sensory)
        summary.update(build_seconds=time.perf_counter()-start,
                       neurons=sim.n_neurons, connections=sim.n_syn, sensory=len(sensory),
                       command=len(command), neural_dt_ms=float(brian2.defaultclock.dt/ms))
        path.write_text(json.dumps(summary, indent=2)+'\n')
        print('constructed full network:', summary['neurons'], summary['connections'], flush=True)
        for refractory in (2.2, 0.0):
            for seed in [int(s) for s in args.seeds.split(',')]:
                sim.reset_state()
                sim.neu.rfc[[sim.flyid2i[f] for f in sensory]] = refractory * ms
                brian2.seed(20000 + seed)
                sim.set_frame_rates([150.] * len(sensory))
                start = time.perf_counter()
                sim.run_frame(args.duration_ms)
                rec = sim.spike_records(command)
                duration = args.duration_ms / 1000
                row = dict(seed=seed, brian_seed=20000+seed, sensory_refractory_ms=refractory,
                           rate_hz=len(rec['t_ms'])/(len(command)*duration),
                           first_spike_ms=float(min(rec['t_ms'])) if len(rec['t_ms']) else None,
                           network_spikes=int(sim.mon_all.num_spikes),
                           run_seconds=time.perf_counter()-start)
                summary['trials'].append(row)
                summary['simulations_executed'] = True
                path.write_text(json.dumps(summary, indent=2)+'\n')
                print(json.dumps(row), flush=True)
        summary['status'] = 'passed'
    except Exception as exc:
        summary.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        path.write_text(json.dumps(summary, indent=2)+'\n')
        raise
    path.write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    main()
