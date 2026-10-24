"""Kinematic feasibility check; not a neural experiment or fitted warning."""
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sim_vision'))
from task_v9 import motion


class WalkOnlyBound(unittest.TestCase):
    def test_contact_by_800ms_for_arbitrary_walk_heading_commands(self):
        # For each precontact segment, triangle inequality gives
        # d_next <= d - (.30-.05)*dt. Here d>=.05>.30*.02.
        for phi in [-60,-30,0,30,60]:
            for seed in range(20):
                rng=np.random.default_rng(seed);fly=np.zeros(2)
                target=.25*np.array([np.cos(np.radians(phi)),np.sin(np.radians(phi))])
                heading=0.;hit=None
                for start in range(0,1000,20):
                    distance=np.linalg.norm(target-fly)
                    fly,target,heading,segments=motion(fly,target,heading,float(rng.uniform(-600,600)),start,start+20,None)
                    self.assertLessEqual(np.linalg.norm(target-fly),distance-.25*.02+1e-12)
                    contacts=[s['contact_ms'] for s in segments if s['contact_ms'] is not None]
                    if contacts:hit=contacts[0];break
                self.assertIsNotNone(hit)
                self.assertLessEqual(hit,800+1e-8)


if __name__=='__main__':unittest.main()
