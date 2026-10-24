import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'sim_vision'))
from task_v9 import burst_active,event_segments,first_contact,motion,input_uniforms,deletion_mask,steering,run


class TaskTests(unittest.TestCase):
    def test_exact_events(self):
        self.assertEqual(event_segments(500,520,260),[(500,510,False),(510,520,True)])
        segments=[q for t in range(0,1000,20) for q in event_segments(t,t+20,260)]
        self.assertEqual(sum(b-a for a,b,on in segments if on),450)
        self.assertFalse(burst_active(1000,300))
        self.assertTrue(burst_active(999.9,300))

    def test_contact_inside_frame(self):
        self.assertAlmostEqual(first_contact([.1,0],[-.1,0]),.25)
        self.assertIsNone(first_contact([.1,.1],[-.1,.1]))

    def test_mirror_motion(self):
        outputs=[]
        for sign in [-1,1]:
            f,t,h,s=motion(np.zeros(2),np.array([.2,sign*.1]),sign*.2,sign*100,0,20,None)
            outputs.append((f,t,h,s))
        np.testing.assert_allclose(outputs[0][0]*[1,-1],outputs[1][0])
        np.testing.assert_allclose(outputs[0][1]*[1,-1],outputs[1][1])
        self.assertAlmostEqual(outputs[0][2],-outputs[1][2])

    def test_stream_pairing_and_nested_masks(self):
        np.testing.assert_array_equal(input_uniforms(1000,0,314),input_uniforms(1000,0,314))
        self.assertFalse(np.array_equal(input_uniforms(1000,0,314),input_uniforms(1000,1,314)))
        a,b=deletion_mask(10000,1000,.25),deletion_mask(10000,1000,.5)
        self.assertFalse(np.any(a&~b))

    def test_no_precue_steering(self):
        c=dict(direction_weights=[1]*8,direction_intercept=0,turn_gain_deg_s=400)
        self.assertEqual(steering(np.ones(8),c,'relay',100),0)

    def test_causal_frame_and_latched_full_exposure(self):
        import pandas as pd
        from types import SimpleNamespace
        class FakeSim:
            w0=np.ones(100)
            flyid2i={i:i for i in range(8)}
            def reset_state(self):
                self.time=0; self.ts=[]; self.ids=[]
                self.mon_all=SimpleNamespace(num_spikes=0)
            def set_frame_rates(self,rates): self.active=np.max(rates)>0
            def run_frame(self,dt):
                if self.active:
                    self.ts.extend([self.time+1]*8); self.ids.extend([0]*8)
                    self.mon_all.num_spikes+=8
                self.time+=dt
            def spike_records(self,ids):
                return dict(t_ms=np.asarray(self.ts),i=np.asarray(self.ids,dtype=int))
        sim=FakeSim();rf=dict(phi_deg=np.array([0]),psi_deg=np.array([0]),w_grad=np.ones(1))
        cmd=pd.DataFrame(dict(flyid=list(range(8))))
        cal=dict(direction_weights=[1]+[0]*7,direction_intercept=0,
                 turn_gain_deg_s=600,trigger_hz=2.5,gate_silent=True)
        r=run(sim,rf,cmd,700,0,'healthy','relay',cal)
        first=next(q for q in r['log'] if q['trigger_ms'] is not None)
        self.assertEqual(first['t_end_ms'],120)
        self.assertEqual(first['heading_deg'],0) # new neural decision did not move this frame
        self.assertLess(r['log'][6]['heading_deg'],0)
        r=run(sim,rf,cmd,700,0,'healthy','disabled',cal)
        self.assertFalse(r['escaped'])
        self.assertLess(r['collision_ms'],1000)
        self.assertEqual(len(r['log']),50)
        self.assertEqual(r['duration_ms'],1000)
        self.assertEqual(r['collision_ms'],r['log'][-1]['collision_ms'])


if __name__=='__main__': unittest.main()
