from pathlib import Path
import sys
import unittest
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/p) for p in ['sim_vision','tools']]
from task_metrics_v9 import sign_flip_p,forecast_margin,mean_interval,bootstrap_indices


class MetricTests(unittest.TestCase):
    def test_preserved_exploratory_interaction(self):
        self.assertEqual(sign_flip_p([0,.5,.5,0,.5,0]),.25)
        self.assertEqual(sign_flip_p([0,0,0]),1.)

    def test_forecast_uses_prefix_state_only(self):
        q=dict(t_end_ms=400,fly=[.02,0],target=[.15,.05],heading_deg=-60,
               next_omega=-100,trigger_ms=180)
        value=forecast_margin(q,250,1000)
        q['future_outcome']='arbitrary'; q['future_spikes']=1e9
        self.assertEqual(value,forecast_margin(q,250,1000))

    def test_bootstrap_preserves_cluster_values(self):
        ix=bootstrap_indices(4,100)
        self.assertEqual(ix.shape,(100,4))
        self.assertEqual(mean_interval([.5]*4,ix),dict(estimate=.5,low=.5,high=.5))


if __name__=='__main__': unittest.main()
