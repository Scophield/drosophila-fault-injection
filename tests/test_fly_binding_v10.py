"""Real saved-manifest regressions; mutations never edit historical files."""
import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from evidence_v10.fly_adapter import FlyAdapter


class FlyBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=FlyAdapter(ROOT/'runs/task-v9-test',ROOT/'runs/task-v9-frozen/calibration.json',ROOT/'runs/task-v9-frozen/registration-core.json')
        cls.digest=next(iter(cls.a.manifests));cls.path=cls.a.manifest_paths[cls.digest]
    def manifest(self):return copy.deepcopy(self.a.manifests[self.digest])
    def test_real_complete_registered_snapshots(self):
        self.assertTrue(all(not v for v in self.a.manifest_issues.values()))
    def test_swapped_worker_entrypoint_even_with_same_neural_hash(self):
        m=self.manifest();m['parameters']['entrypoint_sha256']['tools/run_v9.py']='0'*64
        self.assertTrue(self.a.check_manifest(m,self.path))
    def test_omitted_snapshot_source_is_detected(self):
        m=self.manifest();del m['source_sha256']['sim_vision/task_v9.py']
        self.assertTrue(self.a.check_manifest(m,self.path))
    def test_different_calibration_cannot_claim_same_registration(self):
        m=self.manifest();m['parameters']['calibration_sha256']='f'*64
        self.assertIn('registered calibration',self.a.check_manifest(m,self.path))
    def test_worker_seed_partition_is_allowed(self):
        m=self.manifest();m['parameters']['seeds']=[1000]
        self.assertEqual(self.a.check_manifest(m,self.path),[])


if __name__=='__main__':unittest.main()
