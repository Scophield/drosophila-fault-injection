"""Pure-function and frozen-record checks of the visual encoding formula.

These tests do not import Brian 2, run a neural model, fit parameters or write
experimental records. Scalar degree-domain equations are an independent oracle
for the encoder's vectorized radian-domain Gaussian calculation.
"""
from pathlib import Path
import hashlib
import json
import math
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'sim_vision'),str(ROOT/'tools')]
from closedloop_protocol import retinal_input

FRAME_S=.020
RADIUS_M=.05
COHORTS={
    'RF-0':('runs/task-v9-test','audit/acceptance-v9/core-v2/summary.json'),
    'RF-A':('runs/task-v10-transfer/map-A/test','audit/v10/transfer-01/map-A/analysis/summary.json'),
    'RF-B':('runs/task-v10-transfer/map-B/test','audit/v10/transfer-01/map-B/analysis/summary.json'),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wrap_deg(x):
    return (x+180.)%360.-180.


def degree_oracle(rf,relative,heading,previous,closing,enabled):
    """Scalar equations, using degree-valued angles and seconds throughout."""
    distance=max(math.hypot(*relative),1e-9)
    a=math.degrees(math.atan(RADIUS_M/distance))
    bearing=wrap_deg(math.degrees(math.atan2(relative[1],relative[0]))-math.degrees(heading))
    expansion=(math.degrees(RADIUS_M*closing/(distance*distance+RADIUS_M*RADIUS_M))
               if previous is None else (a-previous)/FRAME_S)
    gain=min(1.,max(0.,max(0.,expansion)/150.*math.exp(-a/60.))) if enabled else 0.
    sigma=max(30.,a)
    rates=[]
    for azimuth,elevation,weight in zip(rf['phi_deg'],rf['psi_deg'],rf['w_grad']):
        square=wrap_deg(float(azimuth)-bearing)**2+float(elevation)**2
        rate=150.*float(weight)*gain*math.exp(-square/(2.*sigma*sigma))
        rates.append(min(150.,max(0.,rate)))
    return np.asarray(rates),dict(half_angle=a,expansion=expansion,u=gain,bearing=bearing,sigma=sigma)


class RetinalFormulaTests(unittest.TestCase):
    def test_initial_analytic_derivative_and_disabled_input(self):
        rf=dict(phi_deg=np.array([0.,30.]),psi_deg=np.array([0.,-20.]),w_grad=np.array([1.,1.4]))
        relative=np.array([.25,0.]);closing=.35
        expected,values=degree_oracle(rf,relative,0.,None,closing,True)
        actual,stimulus=retinal_input(rf,relative,0.,RADIUS_M,FRAME_S,None,closing,enabled=True)
        self.assertAlmostEqual(values['expansion'],math.degrees(.05*.35/(.25**2+.05**2)),places=12)
        np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-12)
        self.assertAlmostEqual(stimulus['u'],values['u'],places=14)
        disabled,stimulus=retinal_input(rf,relative,0.,RADIUS_M,FRAME_S,None,closing,enabled=False)
        self.assertEqual(stimulus['u'],0.)
        np.testing.assert_array_equal(disabled,np.zeros(2))

    def test_first_enabled_frame_uses_the_80_to_100_ms_difference(self):
        folder=ROOT/COHORTS['RF-0'][0]
        record=read(folder/'episodes/proportional_healthy_phi-30_s1000.json')
        current=next(q for q in record['log'] if q['t_ms']==100)
        before=next(q for q in record['log'] if q['t_ms']==80)
        self.assertEqual(before['t_end_ms'],100)
        # The preceding log's positions/heading are state at t=100, but its
        # half-angle was measured at that frame's start, t=80.
        relative=np.array(before['target'])-np.array(before['fly'])
        heading=math.radians(before['heading_deg'])
        closing=.3+.05*math.cos(math.atan2(relative[1],relative[0])-heading)
        rf=dict(phi_deg=np.array([0.]),psi_deg=np.array([0.]),w_grad=np.array([1.]))
        _,expected=degree_oracle(rf,relative,heading,before['half_angle'],closing,True)
        _,actual=retinal_input(rf,relative,heading,RADIUS_M,FRAME_S,before['half_angle'],closing,enabled=True)
        _,wrong_initialization=retinal_input(rf,relative,heading,RADIUS_M,FRAME_S,None,closing,enabled=True)
        self.assertAlmostEqual(expected['u'],current['u'],places=14)
        self.assertAlmostEqual(actual['u'],current['u'],places=14)
        self.assertGreater(abs(wrong_initialization['u']-actual['u']),1e-4)
        self.assertTrue(all(q['u']==0. for q in record['log'] if q['t_ms']<100))

    def test_degree_gaussian_matches_radian_code_with_wrapping_and_both_width_regimes(self):
        rf=dict(phi_deg=np.array([-179.,-90.,0.,90.,179.]),
                psi_deg=np.array([-30.,20.,0.,60.,-10.]),
                w_grad=np.array([1.,1.4,1.,1.8,1.2]))
        seen_widths=set()
        for distance in [.25,.08,.03]:
            for azimuth in [-179.,25.,179.]:
                for heading_deg in [-100.,0.,100.]:
                    relative=distance*np.array([math.cos(math.radians(azimuth)),math.sin(math.radians(azimuth))])
                    angle=math.degrees(math.atan(RADIUS_M/distance));previous=angle-.4
                    heading=math.radians(heading_deg)
                    expected,values=degree_oracle(rf,relative,heading,previous,.3,True)
                    actual,details=retinal_input(rf,relative,heading,RADIUS_M,FRAME_S,previous,.3,enabled=True)
                    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-11)
                    self.assertAlmostEqual(details['phi_now'],values['bearing'],places=12)
                    seen_widths.add(values['sigma']>30.)
        self.assertEqual(seen_widths,{False,True})

    def test_positive_expansion_and_both_clip_ranges(self):
        rf=dict(phi_deg=np.array([0.]),psi_deg=np.array([0.]),w_grad=np.array([1.8]))
        relative=np.array([.25,0.]);a=math.degrees(math.atan(.05/.25))
        shrinking,details=retinal_input(rf,relative,0.,RADIUS_M,FRAME_S,a+1.,.3,enabled=True)
        self.assertEqual(details['u'],0.)
        self.assertEqual(shrinking[0],0.)
        saturated,details=retinal_input(rf,relative,0.,RADIUS_M,FRAME_S,a-10000.,.3,enabled=True)
        self.assertEqual(details['u'],1.)
        self.assertEqual(saturated[0],150.)

    def test_all_576_frozen_episode_frames_match_the_scalar_formula(self):
        episodes=frames=0
        for tag,(folder,summary_name) in COHORTS.items():
            metadata=read(ROOT/folder/'input-map.json')['sensory']
            rf={k:np.array([q[k] for q in metadata]) for k in ['phi_deg','psi_deg','w_grad']}
            summary=read(ROOT/summary_name)
            for name,h in sorted(summary['raw_input_sha256'].items()):
                self.assertEqual(digest(ROOT/name),h)
                record=read(ROOT/name)
                phi=math.radians(record['phi_deg'])
                fly=np.zeros(2);target=.25*np.array([math.cos(phi),math.sin(phi)])
                heading=0.;previous=None
                for q in record['log']:
                    relative=target-fly
                    closing=.3+.05*math.cos(math.atan2(relative[1],relative[0])-heading)
                    enabled=q['t_ms']>=100
                    expected,values=degree_oracle(rf,relative,heading,previous,closing,enabled)
                    actual,details=retinal_input(rf,relative,heading,RADIUS_M,FRAME_S,previous,closing,enabled=enabled)
                    self.assertAlmostEqual(values['u'],q['u'],places=12)
                    self.assertAlmostEqual(values['half_angle'],q['half_angle'],places=12)
                    np.testing.assert_allclose(actual,expected,rtol=0,atol=1e-10)
                    self.assertTrue(np.all((actual>=0)&(actual<=150)))
                    previous=values['half_angle']
                    fly=np.array(q['fly']);target=np.array(q['target'])
                    heading=math.radians(q['heading_deg']);frames+=1
                episodes+=1
        self.assertEqual(episodes,576)
        self.assertEqual(frames,28800)

    def test_encoder_and_task_sources_match_all_seven_generating_batches(self):
        count=0
        for folder,_ in COHORTS.values():
            for manifest_path in (ROOT/folder/'batches').glob('*/run_manifest.json'):
                manifest=read(manifest_path)
                for name in ['sim_vision/closedloop_protocol.py','sim_vision/task_v9.py','sim_vision/encoder.py']:
                    archived=manifest_path.parent/'source'/name
                    self.assertEqual(digest(archived),manifest['source_sha256'][name])
                    self.assertEqual(digest(ROOT/name),digest(archived))
                count+=1
        self.assertEqual(count,7)


if __name__=='__main__':
    unittest.main()
