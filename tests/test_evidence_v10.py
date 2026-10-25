"""Behavioral tests of cross-plant evidence failures, not neural efficacy tests."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_v10.contract import Campaign,audit,prefix,decode_and_audit
from evidence_v10.tank import TankAdapter,run


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter=TankAdapter();s=cls.adapter.spec
        cls.spec=Campaign((9000,),s.conditions,s.laws,s.faults,s.horizon_s,s.frame_s,s.resource_unit)
        cls.raw=[run(9000,c,m,f) for c in s.conditions for m in s.laws for f in s.faults]
    def records(self):return [self.adapter.normalize(copy.deepcopy(r)) for r in self.raw]
    def test_valid_independent_adapter(self):
        self.assertEqual(audit(self.records(),self.spec,self.adapter),[])
    def test_empty_or_duplicate_declarations_cannot_vacuously_pass(self):
        for clusters in [(),(9000,9000)]:
            with self.assertRaises(ValueError):Campaign(clusters,('low',),('relay',),('healthy',),4.,.1,'updates')
    def test_invalid_clock_and_units_rejected_at_declaration(self):
        for horizon,frame,unit in [(float('nan'),.1,'x'),(1.,0.,'x'),(1.,.3,'x'),(1.,.1,'')]:
            with self.assertRaises(ValueError):Campaign((1,),('low',),('relay',),('healthy',),horizon,frame,unit)
    def test_frame_grid_rounding_is_not_exact_actuation(self):
        records=self.records();records[0].native['log'][2]['available_s']=.5
        self.assertIn('adapter-replay',{e.code for e in audit(records,self.spec,self.adapter)})
    def test_nonfinite_decision_timestamp(self):
        records=self.records();records[0].frames[0]['decision_s']=float('nan')
        self.assertIn('invalid-frame-schema',{e.code for e in audit(records,self.spec)})
    def test_native_missing_field_reported_not_silently_dropped(self):
        raw=copy.deepcopy(self.raw);del raw[0]['mask_sha256']
        records,issues=decode_and_audit(raw,self.spec,self.adapter)
        self.assertEqual(len(records),11)
        self.assertIn('native-schema',{e.code for e in issues});self.assertIn('matrix-membership',{e.code for e in issues})
    def test_future_outcome_and_activity_cannot_change_prefix(self):
        r=self.records()[0];expected=prefix(r,.4);r.failure_s=.8;r.success=False
        for q in r.frames:
            if q['end_s']>.4:q['resource']=999999
        self.assertEqual(prefix(r,.4),expected)
    def test_prefix_is_a_copy(self):
        r=self.records()[0];p=prefix(r,.4);p[0]['resource']=999
        self.assertNotEqual(r.frames[0]['resource'],999)
    def test_same_seed_name_does_not_prove_same_random_inputs(self):
        records=self.records();records[1].uniform_sha256='0'*64
        self.assertIn('unpaired-uniforms',{e.code for e in audit(records,self.spec)})
    def test_all_cells_required_even_if_healthy_failure(self):
        records=self.records();records[0].success=False;records[0].failure_s=1.
        self.assertNotIn('matrix-membership',{e.code for e in audit(records,self.spec)})
        records.pop();self.assertIn('matrix-membership',{e.code for e in audit(records,self.spec)})

    def test_forced_dropout_latches_real_boundary_crossing(self):
        # Controlled unit fixture, NOT an independent Monte Carlo sample or a
        # reported tank experiment. Exercise failure semantics absent in the
        # safe 96-record adoption matrix without changing its source/raw data.
        with patch('evidence_v10.tank.mask',return_value=np.ones(40,dtype=bool)):
            row=run(9000,'high','relay','F2_50')
            self.assertFalse(row['success']);self.assertTrue(0<row['failure_s']<4)
            spec=Campaign((9000,),('high',),('relay',),('F2_50',),4.,.1,'valid sensor updates')
            self.assertEqual(audit([self.adapter.normalize(row)],spec,self.adapter),[])
            bad=copy.deepcopy(row);bad['failure_s']+=.01
            self.assertIn('adapter-replay',{e.code for e in audit([self.adapter.normalize(bad)],spec,self.adapter)})


if __name__=='__main__':unittest.main()
