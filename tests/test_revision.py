"""Protocol behavior on synthetic inputs, plus independent archive exposure checks."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'sim_vision'), str(ROOT/'tools')]
from closedloop_protocol import (retinal_input, segment_min_distance, frame_count,
                                 validate_test_keys, validate_calibration)
from calibrate_readout import fit_calibration
from audit_revision import exposure, analyze
from run_closedloop import run_episode, steering_rate


class Geometry(unittest.TestCase):
    def setUp(self):
        self.rf = dict(phi_deg=np.array([-90., 0., 90.]), psi_deg=np.zeros(3), w_grad=np.ones(3))

    def test_heading_rotates_retinal_bearing_and_rates(self):
        a, sa = retinal_input(self.rf, (1., 0.), 0., .05, .02, closing_speed=.3)
        b, sb = retinal_input(self.rf, (1., 0.), np.pi/2, .05, .02, closing_speed=.3)
        self.assertEqual((sa['phi_now'], sb['phi_now']), (0., -90.))
        self.assertEqual(int(a.argmax()), 1)
        self.assertEqual(int(b.argmax()), 0)

    def test_actual_separation_controls_expansion(self):
        _, far = retinal_input(self.rf, (1.,0.), 0, .05, .02, closing_speed=.3)
        approaching, near = retinal_input(self.rf, (.5,0.), 0, .05, .02, far['half_angle'])
        receding, _ = retinal_input(self.rf, (2.,0.), 0, .05, .02, far['half_angle'])
        self.assertGreater(near['half_angle'], far['half_angle'])
        self.assertGreater(approaching.max(), 0)
        self.assertEqual(receding.max(), 0)

    def test_collision_between_frames_is_detected(self):
        self.assertEqual(segment_min_distance((.1,0),(-.1,0)), 0)
        self.assertAlmostEqual(segment_min_distance((.1,.07),(-.1,.07)), .07)
        for duration in (0, -20, 21, float('inf'), float('nan')):
            with self.assertRaises(ValueError):
                frame_count(duration,20)
        self.assertEqual(frame_count(200,20),10)


class Calibration(unittest.TestCase):
    def test_overlap_guard_rejects_keys_and_shared_seed_clusters(self):
        training = {(-30.,0),(-60.,0)}
        for phis in ([-30], [30]):
            with self.assertRaises(ValueError):
                validate_test_keys(phis,[0],training)
        validate_test_keys([-30,30],[6,7],training)
        with self.assertRaises(ValueError):
            validate_calibration({'theta_demo_hz':25.625})

    def test_passive_fit_requires_complete_independent_grid(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[]
            for phi in (-60,-30,0):
                for seed in range(3):
                    row=dict(protocol_version='geometry-v2', mode='observe', evaluation_role='calibration',
                             fault=None,phi_t_deg=phi,seed=seed,rf_seed=20260201,threat_speed=.3,frame_dt_ms=20,
                             log=[dict(t_ms=t,cmd_s={-60:30,-30:20,0:10}[phi],
                                       lr_s={-60:-40,-30:-20,0:2}[phi]) for t in range(0,401,20)])
                    path=Path(d)/f'{phi}_{seed}.json'
                    path.write_text(json.dumps(row)); paths.append(path)
            c=fit_calibration(paths)
            self.assertEqual((c['theta_demo_hz'],c['bias'],c['data_sign'],c['lr_ref']),(25.,2.,1.,42.))
            self.assertEqual(len(c['calibration_keys']),9)
            with self.assertRaises(ValueError): fit_calibration(paths[:-1])
            row['mode']='brain'; paths[-1].write_text(json.dumps(row))
            with self.assertRaises(ValueError): fit_calibration(paths)


class ToySim:
    def __init__(self):
        self.flyid2i={i:i for i in range(8)}
        self.mon_all=SimpleNamespace(num_spikes=0)
    def reset_state(self): self.frames=0; self.mon_all.num_spikes=0
    def set_frame_rates(self,rates): self.rates=rates
    def run_frame(self,dt): self.frames+=1; self.mon_all.num_spikes+=8
    def spike_records(self,ids):
        return dict(t_ms=np.repeat(np.arange(self.frames)*20.+10,8),i=np.tile(np.arange(8),self.frames))


class EpisodeBehavior(unittest.TestCase):
    def setUp(self):
        self.sim=ToySim()
        self.cmd=pd.DataFrame([dict(flyid=i,cell_type=t,side=s) for i,(t,s) in enumerate(
            (t,s) for t in ['DNp01','DNa02','DNp04','DNb01'] for s in ['left','right'])])
        self.rf=dict(phi_deg=np.array([0.]),psi_deg=np.array([0.]),w_grad=np.ones(1))
        self.calib=dict(protocol_version='geometry-v2',theta_demo_hz=10.,lr_ref=1.,bias=0.,data_sign=1.)

    def episode(self,**kw):
        with patch.dict(sys.modules,{'brian2':SimpleNamespace(seed=lambda _:None)}):
            return run_episode(self.sim,self.rf,self.cmd,6,0.,calibration=self.calib,**kw)

    def test_fixed_horizon_does_not_extend_an_active_burst(self):
        r=self.episode(duration_ms=200,threat_speed=.001,burst_delay_ms=0)
        self.assertEqual((len(r['log']),r['duration_ms'],r['termination_reason']),(10,200,'horizon'))
        self.assertTrue(r['burst_active_at_horizon'])
        self.assertTrue(r['escaped'])

    def test_passive_calibration_never_uses_threshold_or_burst(self):
        with patch.dict(sys.modules,{'brian2':SimpleNamespace(seed=lambda _:None)}):
            r=run_episode(self.sim,self.rf,self.cmd,0,0,mode='observe',duration_ms=200,threat_speed=.001)
        self.assertFalse(any(q['burst'] for q in r['log']))
        self.assertTrue(all(q['omega']==0 for q in r['log']))

    def test_collision_truncates_and_is_failure(self):
        r=self.episode(mode='readout_disabled',duration_ms=1000)
        self.assertFalse(r['escaped'])
        self.assertEqual(r['termination_reason'],'collision')
        self.assertLess(r['duration_ms'],1000)
        self.assertLessEqual(r['min_dist'],.05)

    def test_controls_preserve_neural_trigger_and_change_only_steering_law(self):
        self.calib.update(bias=-20.,lr_ref=70.)
        rows={mode:self.episode(mode=mode,duration_ms=200,threat_speed=.001,burst_delay_ms=0)
              for mode in ('brain','precue_gated','bias_only','steer_disabled','readout_disabled')}
        self.assertEqual({rows[m]['trigger_ms'] for m in rows if m!='readout_disabled'},{40.})
        self.assertIsNone(rows['readout_disabled']['trigger_ms'])
        self.assertTrue(all(q['omega']==0 for q in rows['precue_gated']['log'] if q['t_ms']<100))
        self.assertAlmostEqual(rows['brain']['log'][0]['omega'],-400*20/70)
        self.assertTrue(all(q['omega']==rows['brain']['log'][0]['omega'] for q in rows['bias_only']['log']))
        self.assertTrue(all(q['omega']==0 for q in rows['steer_disabled']['log']))
        self.assertNotEqual(steering_rate('brain',30,self.calib,120,0),
                            steering_rate('bias_only',30,self.calib,120,0))

    def test_gate_boundary_and_unknown_mode(self):
        self.calib.update(bias=-20.,lr_ref=70.)
        self.assertEqual(steering_rate('precue_gated',0,self.calib,80,0),0)
        self.assertEqual(steering_rate('precue_gated',0,self.calib,100,0),
                         steering_rate('brain',0,self.calib,100,0))
        with self.assertRaises(ValueError):
            steering_rate('typo',0,self.calib,0,0)


class ArchiveExposure(unittest.TestCase):
    def test_exposure_uses_completed_frame_counts(self):
        e=dict(log=[dict(t_ms=t,n_total=10*(i+1)) for i,t in enumerate(range(0,100,20))])
        self.assertEqual(exposure(e,40)['spikes'],20)
        self.assertEqual(exposure(e)['spikes_per_second'],500)
        with self.assertRaises(ValueError): exposure(e,120)

    def test_archive_split_and_duration_confound_are_reconstructed(self):
        r=analyze(ROOT/'sim_vision/results_vision')
        self.assertEqual([r['healthy_splits'][s]['n'] for s in
                          ('calibration_reuse','nonoverlap_negative','positive_azimuth','frontal')],[6,6,12,3])
        self.assertTrue(all(q['identical_log'] for q in r['calibration_overlap']))
        self.assertAlmostEqual(r['conditions']['F2_50']['median_fixed400_ratio'],.7226281760)
        self.assertGreater(r['conditions']['F2_50']['median_common_ratio'],.7)
        self.assertEqual(r['conditions']['F4_1pct']['sensitivity']['2']['fixed400_ratio'],0)


if __name__=='__main__': unittest.main()
