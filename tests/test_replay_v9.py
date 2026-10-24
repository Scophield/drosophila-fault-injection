"""In-memory mutation tests of ACTUAL validation traces; raw files stay intact."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'sim_vision')]
from replay_audit_v9 import check_record
from task_metrics_v9 import features


class ReplayContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=ROOT/'runs/task-v9-fault-screen'
        record=folder/'episodes/proportional_F2_50_phi-30_s401.json'
        if not record.is_file():raise unittest.SkipTest('actual validation fixture is not bundled')
        cls.record=json.loads(record.read_text())
        cls.mapping=json.loads((folder/'input-map.json').read_text())
        cls.calibration=json.loads((ROOT/'runs/task-v9-frozen/calibration.json').read_text())
        cls.uniforms=[np.random.default_rng(np.random.SeedSequence([20261022,401,k,1])).random(
            (200,len(cls.mapping['pool_flyids'])),dtype=np.float32) for k in range(50)]
        h=hashlib.sha256()
        for u in cls.uniforms:h.update(u.tobytes())
        cls.digest=h.hexdigest()

    def check(self,r):
        return check_record(r,self.calibration,self.mapping,self.uniforms,self.digest)

    def test_actual_failed_validation_trace_replays(self):
        result=self.check(self.record)
        self.assertFalse(result['escaped'])
        self.assertTrue(result['input_events_replayed'])

    def test_heading_mutation_rejected(self):
        r=copy.deepcopy(self.record);r['log'][10]['heading_deg']+=1
        with self.assertRaisesRegex(ValueError,'causal heading'):self.check(r)

    def test_wrong_horizon_flag_and_burst_interval_rejected(self):
        r=copy.deepcopy(self.record);r['burst_active_at_horizon']=not r['burst_active_at_horizon']
        with self.assertRaisesRegex(ValueError,'exact-horizon'):self.check(r)
        r=copy.deepcopy(self.record);r['log'][0]['segments'][0]['burst']=True
        with self.assertRaisesRegex(ValueError,'burst interval'):self.check(r)

    def test_future_outcomes_cannot_change_prefix_metrics(self):
        r=copy.deepcopy(self.record)
        r['escaped']=not r['escaped'];r['collision_ms']=None;r['n_total']=10**9
        for q in r['log']:
            if q['t_end_ms']>400:
                q.update(n_total=10**9,fly=[1e6,1e6],target=[-1e6,-1e6],heading_deg=900)
        self.assertEqual(features(self.record),features(r))


if __name__=='__main__':unittest.main()
