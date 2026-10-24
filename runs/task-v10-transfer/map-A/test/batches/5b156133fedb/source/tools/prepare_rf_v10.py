"""Freeze two independent RF prior draws and a prospective transfer design.

The original hemisphere-constrained azimuth prior, vertical map, cell identities
and Gaussian encoding are retained. Only the independently drawn azimuth
assignment changes. This is sensitivity to an assumed RF prior, not measured RFs.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess

from encoder import load_sensory,build_rf_map
from project_paths import PATH_ANN,PATH_COMP,PATH_CON,MODEL_DIR


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    maps=[]
    for name,seed,dev,val,test,pilot in [('A',2026102301,2000,2200,3000,1900),('B',2026102302,2100,2300,3100,1910)]:
        rf=build_rf_map(load_sensory(),seed=seed)
        rows=rf.to_dict('records')
        for q in rows:q['root_id']=str(q['root_id'])
        p=a.out/f'map-{name}.json'
        p.write_text(json.dumps(dict(map_id=name,rf_seed=seed,generator='unchanged encoder.build_rf_map: independent hemisphere-constrained uniform azimuth draw',rows=rows),indent=2)+'\n')
        maps.append(dict(map_id=name,rf_seed=seed,path=p.as_posix(),sha256=sha(p),pilot_seed=pilot,
            development_seeds=list(range(dev,dev+4)),validation_seeds=list(range(val,val+8)),test_seeds=list(range(test,test+12))))
    design=dict(experiment='rf-transfer-v10.1',created_utc=datetime.now(timezone.utc).isoformat(),
        baseline_commit='43bcd4d6a99b2d9b258cf8a198a4545d237b5c39',git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        maps=maps,phyis_development=[-60.,-30.,0.,30.,60.],phis=[-30.,30.],
        modes=['proportional','relay'],faults=['healthy','F2_25','F2_50'],horizon_ms=1000.,
        calibration=dict(development_episodes=20,horizon_ms=400,training_window_ms=[200,400],ridge_penalty=10,
            turn_gain_deg_s=600,gate_silent=True,trigger='max(2.5, half the 10th percentile of per-episode 200--300-ms development command means)',
            tuning='none: identical fixed recipe for both maps, no fault/test outcomes'),
        validation=dict(clusters=8,episodes=32,role='descriptive capability screen, not map selection',decoder='held-out closed-loop errors reported by whole validation seed; no test fitting'),
        test=dict(clusters_per_map=12,episodes_per_map=144,independent_unit='complete seed, 12 law/bearing/dose cells',
            primary=['per-map healthy-to-fault losses/gains and paired exposure estimands'],
            secondary=['relay-minus-proportional net-loss interaction','frozen validation-derived warning confusion counts'],
            bootstrap=dict(draws=20000,seed=20261023,unit='whole seed within map',interval='95% percentile; conditional on map'),
            multiplicity='interaction sign-flip sensitivity: Holm across both doses and both maps (four tests); no pooling maps or cohorts',
            precision='12 clusters per map is a focused transfer check with wide intervals, not powered confirmation of small interactions'),
        stopping='fixed two maps and 12 test seeds per map; no replacement, test tuning, outcome-based stopping or map selection. Hardware failure/deadline truncation disclosed. Validation failures are retained and limit interpretation.',
        pilot='one 400-ms passive healthy feasibility episode per map; distinct seeds, excluded from fitting and testing. Verify actual resource/input/log integrity before full campaign.',
        scope='independent draws from the SAME assumed RF prior; preserves hemisphere and vertical rules. Does not validate biology, transfer to other RF families, equalize reserve, or establish hardware tolerance.',
        input_sha256={str(p):sha(p) for p in [PATH_ANN,PATH_COMP,PATH_CON,MODEL_DIR/'model.py',Path('sim_vision/encoder.py'),Path(__file__)]})
    (a.out/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    print(json.dumps(dict(design=str(a.out/'design.json'),maps=[{k:q[k] for k in ['map_id','rf_seed','sha256']} for q in maps]),indent=2))


if __name__=='__main__':main()
