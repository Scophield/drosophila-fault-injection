"""Auditable sampled-data task: causal decisions and exact scheduled actuation.

The old geometry-v2 implementation is deliberately preserved for archive replay.
Positions are piecewise linear between logged sub-frame event boundaries.
Heading is integrated at the END of each motion segment; its beginning value
sets that segment's velocity. Collision is exact for this discrete task model.
"""
import hashlib
import numpy as np
from closedloop_protocol import retinal_input, segment_min_distance

VERSION = 'task-v9.1-causal-exact-events'
DT = 20.0
CUE = 100.0
HORIZON = 1000.0
RADIUS = .05
DELAY = 250.0
BURST = 450.0


def burst_active(t, trigger, delay=DELAY, duration=BURST):
    return trigger is not None and trigger + delay <= t < trigger + delay + duration


def event_segments(start, end, trigger, delay=DELAY, duration=BURST):
    boundaries = [start, end]
    if trigger is not None:
        boundaries += [x for x in (trigger+delay, trigger+delay+duration) if start < x < end]
    return [(a, b, burst_active(a, trigger, delay, duration))
            for a, b in zip(sorted(boundaries)[:-1], sorted(boundaries)[1:])]


def first_contact(a, b, radius=RADIUS):
    """Fraction of a linear segment at first sphere contact; None if absent."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b-a
    if np.dot(a,a) <= radius**2:
        return 0.0
    A, B, C = np.dot(d,d), 2*np.dot(a,d), np.dot(a,a)-radius**2
    disc = B*B-4*A*C
    if A == 0 or disc < 0:
        return None
    u = (-B-np.sqrt(max(0.,disc)))/(2*A)
    return float(u) if 0 <= u <= 1 else None


def motion(fly, target, heading, omega, start, end, trigger,
           threat_speed=.3, delay=DELAY):
    segments=[]
    for a,b,burst in event_segments(start,end,trigger,delay):
        dt=(b-a)/1000
        before=target-fly
        vf=(.35 if burst else .05)*np.array([np.cos(heading),np.sin(heading)])
        vt=-threat_speed*before/max(np.linalg.norm(before),1e-12)
        fly=fly+vf*dt; target=target+vt*dt
        after=target-fly
        contact=first_contact(before,after)
        segments.append(dict(start_ms=a,end_ms=b,burst=burst,
            min_distance=segment_min_distance(before,after),
            contact_ms=None if contact is None else a+(b-a)*contact))
        if not burst:
            heading=float(np.clip(heading+np.radians(omega)*dt,-np.radians(100),np.radians(100)))
    return fly,target,heading,segments


def input_uniforms(seed, frame, n_inputs, n_steps=200):
    # No generator state can depend on controller, damage, firing, or stopping.
    return np.random.default_rng(np.random.SeedSequence([20261022,seed,frame,1])).random(
        (n_steps,n_inputs), dtype=np.float32)


def deletion_mask(n, seed, fraction):
    return np.random.default_rng(np.random.SeedSequence([20261022,seed,2])).random(n)<fraction


def mask_hash(mask):
    return hashlib.sha256(np.packbits(mask).tobytes()).hexdigest()


def steering(features, calibration, mode, t):
    if mode == 'observe' or t <= CUE:
        return 0.
    if calibration.get('gate_silent',False) and float(np.mean(features)) < calibration['trigger_hz']:
        return 0.
    # Calibration defines a linear bearing score, not a measured biological map.
    score=float(np.dot(features,calibration['direction_weights'])+calibration['direction_intercept'])
    gain=calibration['turn_gain_deg_s']
    if mode == 'proportional':
        return -gain*float(np.clip(score,-1,1))
    if mode == 'relay':
        return -gain*float(np.sign(score))
    if mode == 'disabled':
        return 0.
    raise ValueError(mode)


def run(sim, rf_map, cmd_df, seed, phi, fault, mode, calibration,
        horizon=HORIZON, threat_speed=.3, delay=DELAY):
    sim.reset_state()
    fraction={'healthy':0.,'F2_25':.25,'F2_50':.5}[fault]
    mask=deletion_mask(len(sim.w0),seed,fraction)
    if fraction:
        sim.apply_weights(np.where(mask,0.,sim.w0))
    sim.input_seed=seed; sim.input_frame=0
    sim.uniform_hash=hashlib.sha256(); sim.event_hash=hashlib.sha256()
    fly=np.zeros(2); target=.25*np.array([np.cos(np.radians(phi)),np.sin(np.radians(phi))])
    heading=0.; previous_angle=None; trigger=None; collision=None; omega=0.
    history=[]; log=[]; min_distance=.25
    ro_idx=np.array([sim.flyid2i[int(f)] for f in cmd_df.flyid],dtype=np.int64)
    for k in range(int(round(horizon/DT))):
        t=k*DT; end=t+DT; relative=target-fly
        rates,stimulus=retinal_input(rf_map,relative,heading,RADIUS,DT/1000,previous_angle,
            threat_speed+.05*np.cos(np.arctan2(relative[1],relative[0])-heading), enabled=t>=CUE)
        previous_angle=stimulus['half_angle']
        sim.set_frame_rates(rates); sim.run_frame(DT)
        rec=sim.spike_records(cmd_df.flyid.tolist())
        ids=rec['i'][(rec['t_ms']>=t-1e-8)&(rec['t_ms']<end-1e-8)]
        counts=np.array([np.sum(ids==idx) for idx in ro_idx])
        feature=counts/(DT/1000); history.append(feature)
        smooth=np.mean(history[-5:],axis=0)
        # Only decisions available at t can influence [t,end). New decisions
        # below apply to the following frame. Continue after contact with a
        # latched failure flag so the neural resource endpoint always has 1 s.
        fly,target,heading,segments=motion(fly,target,heading,omega,t,end,trigger,threat_speed,delay)
        min_distance=min(min_distance,*[q['min_distance'] for q in segments])
        if collision is None:
            collision=next((q['contact_ms'] for q in segments if q['contact_ms'] is not None),None)
        cmd=float(np.mean(smooth))
        if mode!='observe' and trigger is None and end>CUE and cmd>=calibration['trigger_hz']:
            trigger=end
        omega=steering(smooth,calibration,mode,end) if mode!='observe' else 0.
        log.append(dict(t_ms=t,t_end_ms=end,n_total=int(sim.mon_all.num_spikes),
            cmd_rates=feature.tolist(),smooth_rates=smooth.tolist(),cmd_hz=cmd,
            phi_now=stimulus['phi_now'],u=stimulus['u'],half_angle=stimulus['half_angle'],
            distance=float(np.linalg.norm(target-fly)),heading_deg=float(np.degrees(heading)),
            fly=fly.tolist(),target=target.tolist(),next_omega=omega,
            trigger_ms=trigger,collision_ms=collision,segments=segments))
    return dict(protocol=VERSION,seed=seed,phi_deg=phi,fault=fault,mode=mode,
        horizon_ms=horizon,duration_ms=horizon,collision_ms=collision,escaped=collision is None,
        min_distance=min_distance,trigger_ms=trigger,burst_delay_ms=delay,burst_duration_ms=BURST,
        burst_active_at_horizon=burst_active(horizon,trigger,delay),
        n_total=int(sim.mon_all.num_spikes),mask_sha256=mask_hash(mask),deleted_rows=int(mask.sum()),
        uniform_sha256=sim.uniform_hash.hexdigest(),event_sha256=sim.event_hash.hexdigest(),
        command_flyids=[int(f) for f in cmd_df.flyid],log=log)
