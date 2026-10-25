"""Re-score immutable archived records; never run a simulator or alter inputs."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
THETA = 51.4
N_BOOT = 20000
BOOT_SEED = 0


def load(path):
    rows = [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    trials = [r['trial'] for r in rows]
    if len(set(trials)) != len(trials) or not rows:
        raise ValueError(f'empty or duplicate trials: {path}')
    return sorted(rows, key=lambda r: r['trial'])


def summarize(rows):
    rates = np.array([r['pop_rate'] for r in rows])
    spikes = np.array([r['n_total_spikes'] for r in rows])
    idx = np.random.default_rng(BOOT_SEED).integers(0, len(rows), (N_BOOT, len(rows)))
    ci = np.percentile(np.median(rates[idx], axis=1), [2.5, 97.5]).tolist()
    lat = [r['latency_ms'] for r in rows if r.get('latency_ms') is not None]
    return dict(n=len(rows), rate_med=float(np.median(rates)), rate_p10=float(np.percentile(rates, 10)),
                rate_p90=float(np.percentile(rates, 90)), rate_ci95=ci, tot_med=float(np.median(spikes)),
                tot_mean=float(np.mean(spikes)), lat_med=float(np.median(lat)) if lat else None,
                transmission_pass=int(np.sum(rates >= THETA)))


def protocols(core, ctrl, baseline):
    br, bt = baseline['rate_med'], baseline['tot_med']
    selected = {p.stem: p for p in sorted(core.glob('*.jsonl')) if p.stem != 'healthy'}
    control_dirs = [ctrl] if isinstance(ctrl, Path) else ctrl
    for folder in control_dirs:
        for p in sorted(folder.glob('*.jsonl')):
            if p.stem.startswith(('HUB_', 'EIm_', 'INHrand_')):
                if p.stem in selected:
                    raise ValueError(f'duplicate condition across sources: {p.stem}')
                selected[p.stem] = p
    conditions = []
    for name, p in selected.items():
        rs = load(p)
        if len(rs) != 12 or {r['trial'] for r in rs} != set(range(12)):
            raise ValueError(f'expected 12 complete trials: {p}')
        trans = [r['trial'] for r in rs if r['pop_rate'] >= THETA]
        failed = [dict(trial=r['trial'], spikes=r['n_total_spikes'],
                       spikes_ratio=r['n_total_spikes']/bt, rate_ratio=r['pop_rate']/br)
                  for r in rs if r['pop_rate'] >= THETA and
                  (r['pop_rate'] > 2*br or r['n_total_spikes'] > 2*bt)]
        conditions.append(dict(name=name, trials=len(rs), transmission=len(trans),
                               envelope=len(trans)-len(failed), additional_failures=failed,
                               source=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)))
    return dict(definition='transmission-only re-scoring, not execution of SpikeFI or SpikingJET',
                theta_hz=THETA, envelope=2, baseline_rate_hz=br, baseline_spikes=bt,
                trials=sum(c['trials'] for c in conditions),
                transmission_only_pass=sum(c['transmission'] for c in conditions),
                envelope_pass=sum(c['envelope'] for c in conditions), conditions=conditions)


def paired_episodes(vision):
    def episodes(tag, fault, mode='brain'):
        result = {}
        for p in sorted((vision / f'episodes_{tag}').glob(f'{mode}_{fault}_phi*_s*.json')):
            e = json.loads(p.read_text())
            key = (float(e['phi_t_deg']), int(e['seed']))
            if key in result:
                raise ValueError(f'duplicate episode {key}')
            result[key] = (p, e)
        return result
    healthy = episodes('v4', 'healthy')
    main_keys={(float(phi),seed) for phi in (-60,-30,30,60) for seed in range(6)}
    if not main_keys <= set(healthy):
        raise ValueError('incomplete 24-episode healthy test grid')
    fault_keys={(float(phi),seed) for phi in (-60,-30,30,60) for seed in range(3)}
    output = {'healthy_summary':dict(n=len(main_keys),escaped=sum(healthy[k][1]['escaped'] for k in main_keys))}
    frontal={(0.,seed) for seed in range(3)}
    if not frontal <= set(healthy):
        raise ValueError('incomplete frontal grid')
    output['frontal_summary']=dict(n=3,escaped=sum(healthy[k][1]['escaped'] for k in frontal))
    for mode in ('steer_disabled','readout_disabled','flip','handrule'):
        control=episodes('v4','healthy',mode)
        if set(control)!=fault_keys:
            raise ValueError(f'incomplete or extra control episodes: {mode}')
        output[f'control/{mode}']=dict(n=12,escaped=sum(e['escaped'] for _,e in control.values()))
    for tag, fault in [('v4','F4_1pct'), ('v4','F2_25'), ('v4','F2_50'), ('v4c','HUB_inh')]:
        faulted = episodes(tag, fault)
        if set(faulted)!=fault_keys:
            raise ValueError(f'incomplete or extra fault episodes: {tag}/{fault}')
        pairs = []
        for key, (path, e) in sorted(faulted.items()):
            if key not in healthy:
                raise ValueError(f'no healthy pair for {path}')
            _, h = healthy[key]
            pairs.append(dict(phi=key[0], seed=key[1], ratio=e['n_total']/h['n_total'],
                              escaped=e['escaped'], burst=any(r['burst'] for r in e['log']),
                              spikes=e['n_total'], healthy_spikes=h['n_total'],
                              heading=abs(e['log'][-1]['heading_deg']),
                              healthy_heading=abs(h['log'][-1]['heading_deg'])))
        if not pairs:
            raise ValueError(f'missing episodes {tag}/{fault}')
        output[f'{tag}/{fault}'] = dict(pairs=pairs, n=len(pairs),
            escaped=sum(r['escaped'] for r in pairs), bursts=sum(r['burst'] for r in pairs),
            activity_exceedances=sum(r['ratio'] > 2 for r in pairs),
            median_pair_ratio=float(np.median([r['ratio'] for r in pairs])),
            ratio_of_paired_medians=float(np.median([r['spikes'] for r in pairs]) /
                                         np.median([r['healthy_spikes'] for r in pairs])),
            median_spikes=float(np.median([r['spikes'] for r in pairs])),
            median_heading=float(np.median([r['heading'] for r in pairs])),
            healthy_median_heading=float(np.median([r['healthy_heading'] for r in pairs])))
    return output


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--run-root', type=Path, help='completed NEW run tree; omit to audit shipped archive')
    args = ap.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit('output must be empty; choose a new audit directory')
    args.out.mkdir(parents=True, exist_ok=True)
    core_root = args.run_root/'core' if args.run_root else ROOT/'sim/results'
    core = core_root/'real'
    ctrl_dirs = [args.run_root/'controls', args.run_root/'inhib_controls'] if args.run_root else [ROOT/'sim_vision/results_vision/openloop_controls']
    vision = args.run_root/'vision' if args.run_root else ROOT/'sim_vision/results_vision'
    summary = {phase: {p.stem: summarize(load(p)) for p in sorted((core_root/phase).glob('*.jsonl'))}
               for phase in ('real','er','real_fix','real_legacy')}
    for phase in ('real','er'):
        if len(summary[phase]) != 19 or any(v['n'] != 12 for v in summary[phase].values()):
            raise ValueError(f'incomplete main sweep: {phase}')
    controls = {}
    for folder in ctrl_dirs:
        for p in sorted(folder.glob('*.jsonl')):
            if p.stem in controls:
                raise ValueError(f'duplicate control {p}')
            controls[p.stem] = summarize(load(p))
    expected_controls={f'{name}_d{drive}' for name in ('healthy','F2_50','F4_1pct') for drive in (75,150,300)}
    expected_controls.update(('EIm_1pct','EIm_2pct','HUB_inh','HUB_exc','INHrand_cells','INHrand_mass'))
    if not expected_controls <= set(controls) or any(controls[k]['n']!=12 for k in expected_controls):
        raise ValueError('incomplete 15-condition drive/sign-control grid')
    baseline = summary['real']['healthy']
    dropout = []
    for f in (.05,.10,.25,.50):
        retention = summary['real'][f'F2_drop_{int(100*f):02d}']['rate_med']/baseline['rate_med']
        dropout.append(dict(deleted=f, surviving=1-f, retention=retention, retention_over_survival=retention/(1-f)))
    hs = {'healthy': baseline, 'F4_1pct': summary['real']['F4_hub_1pct']}
    hs.update({k: controls[k] for k in ('HUB_inh','HUB_exc','INHrand_mass')})
    hub_sign = {k: dict(tot=v['tot_med'], rate=v['rate_med'], n=v['n']) for k,v in hs.items()}
    damage = {phase: {p.stem: sorted({r['frac_edges_modified'] for r in load(p)})
              for p in sorted((core_root/phase).glob('F4*.jsonl'))} for phase in summary}
    outputs = {'summary.json': summary, 'bootstrap_controls.json': controls,
               'protocol_scores.json': protocols(core,ctrl_dirs,baseline), 'dropout.json': dropout,
               'closedloop_pairs.json': paired_episodes(vision), 'hub_sign.json': hub_sign,
               'hub_damage_archive.json': damage}
    sources = sorted(set(list(core_root.rglob('*.jsonl')) + [p for d in ctrl_dirs for p in d.glob('*.jsonl')] +
                         list(vision.glob('episodes_v4/*.json')) + list(vision.glob('episodes_v4c/*.json'))))
    manifest = dict(base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    bootstrap=dict(unit='trial record within each condition',statistic='median',
                                   repetitions=N_BOOT,seed=BOOT_SEED,interval='percentile 2.5--97.5'),
                    python=sys.version,numpy=np.__version__,created_utc=datetime.now(timezone.utc).isoformat(),
                    source_sha256={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                    caveat='archive re-analysis only; corrected hub selection not rerun; old hub identities unavailable' if not args.run_root else
                           'new run re-analysis; compare actual hub manifests before interpreting cross-backend differences')
    for name, obj in {**outputs,'manifest.json':manifest}.items():
        (args.out/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(dropout=dropout,protocol_totals={k:outputs['protocol_scores.json'][k]
                     for k in ('trials','transmission_only_pass','envelope_pass')},
                     hub_inh=controls['HUB_inh'],closedloop={k:{x:v for x,v in d.items() if x!='pairs'}
                     for k,d in outputs['closedloop_pairs.json'].items()}),indent=2))


if __name__ == '__main__':
    main()
