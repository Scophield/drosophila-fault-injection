"""Regressions for malformed core fields; fixtures are not scientific samples."""
import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_v10.contract import Campaign,audit,decode_and_audit
from evidence_v10.tank import TankAdapter,run


class SchemaBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter=TankAdapter();s=cls.adapter.spec
        cls.spec=Campaign((9000,),s.conditions,s.laws,s.faults,s.horizon_s,s.frame_s,s.resource_unit)
        cls.rows=[run(9000,c,m,f) for c in s.conditions for m in s.laws for f in s.faults]

    def test_clean_campaign_still_passes(self):
        valid,issues=decode_and_audit(copy.deepcopy(self.rows),self.spec,self.adapter)
        self.assertEqual(len(valid),12);self.assertEqual(issues,[])

    def test_three_reported_native_crashes_are_indexed_findings(self):
        for field,value in [('uniform_sha256',None),('mask_sha256',123),('seed',[])]:
            with self.subTest(field=field):
                rows=copy.deepcopy(self.rows);rows[4][field]=value
                valid,issues=decode_and_audit(rows,self.spec,self.adapter)
                self.assertEqual(len(valid),11)
                self.assertTrue(any(x.code=='native-schema' and 'row 4:' in x.detail for x in issues))
                self.assertIn('matrix-membership',{x.code for x in issues})

    def test_mixed_batch_retains_valid_rows_and_each_bad_row_index(self):
        rows=copy.deepcopy(self.rows)
        for i,field,value in [(0,'uniform_sha256',None),(4,'mask_sha256',123),(8,'seed',[])]:rows[i][field]=value
        valid,issues=decode_and_audit(rows,self.spec,self.adapter)
        self.assertEqual(len(valid),9)
        details=[x.detail for x in issues if x.code=='native-schema']
        self.assertEqual(len(details),3)
        for i in [0,4,8]:self.assertTrue(any(f'row {i}:' in d for d in details))
        self.assertIn('matrix-membership',{x.code for x in issues})
        self.assertFalse(any(x.code=='adapter-replay' for x in issues))

    def test_direct_normalized_entry_is_guarded_before_sets_and_regex(self):
        for field,value in [('cluster',[]),('condition',{}),('uniform_sha256',None),('mask_sha256',123),
            ('success','yes'),('deleted',[]),('bindings',None),('frames',[None]),('native',None),
            ('frame_s','0.1'),('failure_s',[])]:
            with self.subTest(field=field):
                records=[self.adapter.normalize(copy.deepcopy(r)) for r in self.rows]
                setattr(records[0],field,value)
                issues=audit(records,self.spec,self.adapter)
                self.assertTrue(any(x.code=='record-schema' and 'row 0:' in x.detail for x in issues))
                self.assertIn('matrix-membership',{x.code for x in issues})

    def test_nonboolean_native_success_is_not_coerced(self):
        for value in ['yes',1,None,[]]:
            with self.subTest(value=value):
                rows=copy.deepcopy(self.rows);rows[0]['success']=value
                valid,issues=decode_and_audit(rows,self.spec,self.adapter)
                self.assertEqual(len(valid),11)
                self.assertTrue(any(x.code=='native-schema' and 'success must be boolean' in x.detail for x in issues))

    def test_schema_failure_does_not_hide_other_record_errors(self):
        rows=copy.deepcopy(self.rows);rows[0]['seed']=[];rows[1]['log'][0]['available_s']=-.1
        valid,issues=decode_and_audit(rows,self.spec,self.adapter)
        self.assertEqual(len(valid),11)
        codes={x.code for x in issues}
        self.assertTrue({'native-schema','matrix-membership','decision-availability','adapter-replay'}<=codes)

    def test_invalid_digest_text_keeps_semantic_issue(self):
        records=[self.adapter.normalize(copy.deepcopy(r)) for r in self.rows]
        records[0].uniform_sha256='invalid'
        self.assertIn('invalid-digest',{x.code for x in audit(records,self.spec,self.adapter)})

    def test_extreme_numeric_frame_is_a_finding(self):
        records=[self.adapter.normalize(copy.deepcopy(r)) for r in self.rows]
        records[0].frames[0]['decision_s']=10**1000
        self.assertIn('invalid-frame-schema',{x.code for x in audit(records,self.spec)})

    def test_same_type_guards_apply_to_saved_fly_rows(self):
        import json
        from evidence_v10.fly_adapter import FlyAdapter
        adapter=FlyAdapter(ROOT/'runs/task-v9-test',ROOT/'runs/task-v9-frozen/calibration.json',
            ROOT/'runs/task-v9-frozen/registration-core.json')
        original=json.loads((ROOT/'runs/task-v9-test/episodes/proportional_F2_50_phi-30_s1000.json').read_text())
        spec=Campaign((1000,),(-30.,),('proportional',),('F2_50',),1.,.02,'network spikes')
        for field,value in [('uniform_sha256',None),('mask_sha256',123),('seed',[])]:
            with self.subTest(field=field):
                row=copy.deepcopy(original);row[field]=value
                valid,issues=decode_and_audit([row],spec,adapter)
                self.assertEqual(valid,[])
                self.assertTrue(any(x.code=='native-schema' and 'row 0:' in x.detail for x in issues))
                self.assertIn('matrix-membership',{x.code for x in issues})


if __name__=='__main__':unittest.main()
