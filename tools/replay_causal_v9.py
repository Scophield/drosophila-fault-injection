"""Secondary causal-control geometry/decision/input replay; does not simulate neural dynamics.

Uses recorded command spikes, source-bound maps and seed streams. It verifies
trace and input consistency, NOT the correctness of the whole-neuron simulator.
No task_v9/vision_v9 implementation is imported here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def close(a,b,label,atol=1e-9):
    if not np.allclose(a,b,rtol=0,atol=atol): raise ValueError(f'{label}: {a} != {b}')


def first_hit(a,b):
    if a@a<=.05**2:return 0.
    d=b-a;A=d@d;B=2*(a@d);C=a@a-.05**2;disc=B*B-4*A*C
    if A==0 or disc<0:return None
    root=(-B-np.sqrt(disc))/(2*A)
    return float(root) if 0<=root<=1 else None


def check_record(r,cal,input_map,uniforms,uniform_digest):
    if r['uniform_sha256']!=uniform_digest: raise ValueError('uniform stream digest')
    pool={f:i for i,f in enumerate(input_map['pool_flyids'])}
    sensory=input_map['sensory'];positions=[pool[s['flyid']] for s in sensory]
    rfphi=np.array([s['phi_deg'] for s in sensory]);rfpsi=np.array([s['psi_deg'] for s in sensory])
    grad=np.array([s['w_grad'] for s in sensory]);n=len(pool)
    if [str(f) for f in r['command_flyids']]!=[c['flyid'] for c in input_map['commands']]:
        raise ValueError('command ID/order mismatch')
    fly=np.zeros(2);target=.25*np.array([np.cos(np.radians(r['phi_deg'])),np.sin(np.radians(r['phi_deg']))])
    heading=0.;omega=0.;trigger=None;hit=None;minimum=.25;angle_previous=None;history=[];last_total=0
    event_digest=hashlib.sha256();burst_ms=0.
    if len(r['log'])!=50:raise ValueError('not a complete 1-s trace')
    for k,q in enumerate(r['log']):
        start=k*20.;end=start+20
        close([q['t_ms'],q['t_end_ms']],[start,end],'clock')
        relative=target-fly;distance=max(float(np.linalg.norm(relative)),1e-9)
        phi=(np.degrees(np.arctan2(relative[1],relative[0]))-np.degrees(heading)+180)%360-180
        angle=float(np.degrees(np.arctan(.05/distance)))
        close(phi,q['phi_now'],'body-frame bearing');close(angle,q['half_angle'],'actual-separation angle')
        expansion=0 if angle_previous is None else (angle-angle_previous)/.02
        gain=0. if start<100 else float(np.clip(max(0,expansion)/150*np.exp(-angle/60),0,1))
        close(gain,q['u'],'looming expansion/cue');angle_previous=angle
        dphi=np.radians((rfphi-q['phi_now']+180)%360-180);dpsi=np.radians(rfpsi)
        sigma=np.radians(max(30.,q['half_angle']))
        rates=np.clip(150*grad*np.exp(-(dphi**2+dpsi**2)/(2*sigma**2))*q['u'],0,150)
        base=np.zeros(n);base[positions]=rates
        tt,ii=np.nonzero(uniforms[k]<base[None,:]*.0001)
        event_digest.update(np.column_stack([tt,ii]).astype('<i4').tobytes())
        cuts=[start,end]
        if trigger is not None:cuts += [v for v in [trigger+250,trigger+700] if start<v<end]
        cuts=sorted(cuts)
        if len(q['segments'])!=len(cuts)-1:raise ValueError('wrong event partition')
        for (a,b),observed in zip(zip(cuts[:-1],cuts[1:]),q['segments']):
            on=trigger is not None and trigger+250<=a<trigger+700
            close([observed['start_ms'],observed['end_ms']],[a,b],'segment clock')
            if observed['burst']!=on:raise ValueError('burst interval')
            dt=(b-a)/1000;before=target-fly
            vf=(.35 if on else .05)*np.array([np.cos(heading),np.sin(heading)])
            vt=-.3*before/max(float(np.linalg.norm(before)),1e-12)
            fly+=vf*dt;target+=vt*dt;after=target-fly
            delta=after-before;norm2=float(delta@delta)
            s=float(np.clip(-before@delta/norm2,0,1)) if norm2 else 0.
            separation=float(np.linalg.norm(before+s*delta));minimum=min(minimum,separation)
            close(separation,observed['min_distance'],'within-segment minimum')
            u=first_hit(before,after)
            contact=None if u is None else a+u*(b-a)
            if (contact is None)!=(observed['contact_ms'] is None):raise ValueError('within-segment contact')
            if contact is not None:
                close(contact,observed['contact_ms'],'contact time',1e-6)
                if hit is None:hit=contact
            if not on:heading=float(np.clip(heading+np.radians(omega)*dt,-np.radians(100),np.radians(100)))
            else:burst_ms+=b-a
        close(fly,q['fly'],'causal fly motion');close(target,q['target'],'simultaneous pursuit')
        close(np.degrees(heading),q['heading_deg'],'causal heading')
        close(np.linalg.norm(target-fly),q['distance'],'separation log')
        if (hit is None)!=(q['collision_ms'] is None):raise ValueError('latched collision')
        if hit is not None:close(hit,q['collision_ms'],'latched time',1e-6)
        if q['n_total']<last_total:raise ValueError('spike count decreased')
        close(np.array(q['cmd_rates'])*.02,np.rint(np.array(q['cmd_rates'])*.02),'integer command spikes')
        if np.sum(q['cmd_rates'])*.02>q['n_total']-last_total+1e-8:raise ValueError('command count exceeds all spikes')
        last_total=q['n_total'];history.append(np.array(q['cmd_rates']))
        smooth=np.mean(history[-5:],axis=0);command=float(np.mean(smooth))
        close(smooth,q['smooth_rates'],'readout smoothing');close(command,q['cmd_hz'],'readout mean')
        if r['mode']!='observe' and trigger is None and end>100 and command>=cal['trigger_hz']:trigger=end
        if q['trigger_ms']!=trigger:raise ValueError('trigger decision time')
        if r['mode'] in ['observe','disabled'] or end<=100 or command<cal['trigger_hz']:omega=0.
        else:
            score=float(smooth@np.array(cal['direction_weights'])+cal['direction_intercept'])
            omega=-cal['turn_gain_deg_s']*(float(np.clip(score,-1,1)) if r['mode']=='proportional' else float(np.sign(score)))
        close(omega,q['next_omega'],'next-frame control law')
    if r['escaped']!=(hit is None):raise ValueError('task outcome')
    if hit is not None:close(hit,r['collision_ms'],'final collision',1e-6)
    close(minimum,r['min_distance'],'final minimum')
    expected=trigger is not None and trigger+250<=1000<trigger+700
    if r['burst_active_at_horizon']!=expected:raise ValueError('exact-horizon burst state')
    if event_digest.hexdigest()!=r['event_sha256']:raise ValueError('actual input event stream digest')
    if r['n_total']!=last_total:raise ValueError('total spike accounting')
    return dict(seed=r['seed'],phi_deg=r['phi_deg'],mode=r['mode'],fault=r['fault'],
        escaped=r['escaped'],burst_ms=burst_ms,geometry_passed=True,input_events_replayed=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--calibration',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,help='Explicit validation/debug subset only')
    args=ap.parse_args();t=time.perf_counter()
    cal=json.loads(args.calibration.read_text());map_path=args.root/'input-map.json'
    input_map=json.loads(map_path.read_text());map_digest=hashlib.sha256(map_path.read_bytes()).hexdigest()
    paths=sorted((args.root/'episodes').glob('*.json'));pairs=[(p,json.loads(p.read_text())) for p in paths]
    if args.seed is not None:pairs=[(p,r) for p,r in pairs if r['seed']==args.seed]
    if not pairs:raise ValueError('no selected actual records')
    results=[]
    for seed in sorted({r['seed'] for _,r in pairs}):
        uniforms=[np.random.default_rng(np.random.SeedSequence([20261022,seed,k,1])).random(
            (200,len(input_map['pool_flyids'])),dtype=np.float32) for k in range(50)]
        digest=hashlib.sha256()
        for u in uniforms:digest.update(u.tobytes())
        selected=[r for _,r in pairs if r['seed']==seed]
        row_uniform=np.random.default_rng(np.random.SeedSequence([20261022,seed,2])).random(selected[0]['n_connection_rows'])
        masks={}
        for fault,fraction in [('healthy',0.),('F2_25',.25),('F2_50',.5)]:
            mask=row_uniform<fraction
            masks[fault]=(hashlib.sha256(np.packbits(mask).tobytes()).hexdigest(),int(mask.sum()))
        for p,r in pairs:
            if r['seed']!=seed:continue
            if r['input_map_sha256']!=map_digest:raise ValueError('input map hash')
            if r['calibration_sha256']!=hashlib.sha256(args.calibration.read_bytes()).hexdigest():raise ValueError('calibration hash')
            if (r['mask_sha256'],r['deleted_rows'])!=masks[r['fault']]:raise ValueError('fault mask replay')
            if 'deleted_exc_rows' in r and sum(r[k] for k in ['deleted_exc_rows','deleted_inh_rows','deleted_zero_rows'])!=r['deleted_rows']:
                raise ValueError('damage sign accounting')
            check=check_record(r,cal,input_map,uniforms,digest.hexdigest())
            check['file_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();check['file']=p.as_posix()
            results.append(check)
    args.out.mkdir(parents=True,exist_ok=False)
    report=dict(passed=True,records=len(results),seed_clusters=len({r['seed'] for r in results}),
        scope='validation/debug subset' if args.seed is not None else 'all supplied records',
        checks='independent sampled geometry, retinal expansion, readout/decision causality, exact actuation, latched collision, complete exposure, fault masks and input-event/uniform replay',
        neural_dynamics_resimulated=False,seconds=time.perf_counter()-t,
        audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records_checked=results)
    (args.out/'replay.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records_checked'},indent=2))


if __name__=='__main__':main()
