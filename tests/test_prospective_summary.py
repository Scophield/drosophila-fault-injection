"""A completed synthetic matrix must retain calibration and endpoint provenance."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import summarize_prospective as summary


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProspectiveSummary(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(patch.stopall)
        patch.object(summary, 'ROOT', self.root).start()
        source = self.root/'vision/episodes_calibration/source.json'
        source_hash = write_json(source, {'phi_t_deg': 0, 'seed': 0})
        self.calibration = self.root/'vision/calib.json'
        calibration_hash = write_json(self.calibration, dict(
            protocol_version='geometry-v2', theta_demo_hz=10, lr_ref=20,
            bias=0, data_sign=1, calibration_keys=[dict(phi=0, seed=0)],
            frame_dt_ms=20, rf_seed=42, threat_speed=.3,
            source_sha256={str(source): source_hash}))
        parameters = dict(evaluation_role='test', calibration_sha256=calibration_hash,
                          modes='brain', phis='30', seeds='6', faults='none', duration_ms=1000,
                          frame_dt_ms=20, rf_seed=42, threat_speed=.3)
        manifest = dict(parameters=parameters, runtime_backend='numpy', neural_dt_ms=.1)
        manifest_hash = write_json(self.root/'vision/batches/test/run_manifest.json', manifest)
        self.episode = self.root/'vision/episodes_evaluation/brain.json'
        self.row = dict(mode='brain', fault=None, phi_t_deg=30, seed=6,
                        protocol_version='geometry-v2', evaluation_role='test',
                        calibration_sha256=calibration_hash,
                        run_manifest_sha256=manifest_hash, horizon_ms=1000,
                        frame_dt_ms=20, rf_seed=42, threat_speed=.3,
                        termination_reason='horizon', escaped=True, duration_ms=1000,
                        burst_active_at_horizon=False, log=[dict(t_end_ms=1000)])
        write_json(self.episode, self.row)

    def summarize(self):
        return summary.summarize(self.root, self.calibration, [6], [30], faults=(None,))

    def test_complete_declared_matrix_retains_generation_manifest(self):
        result = self.summarize()
        self.assertEqual(result['groups']['brain/healthy']['collision_free'], 1)
        self.assertEqual(len(result['generation_manifests']), 1)
        self.assertEqual(len(result['source_sha256']), 1)

    def test_missing_scenario_is_not_a_completed_matrix(self):
        self.episode.unlink()
        with self.assertRaisesRegex(ValueError, 'matrix mismatch'):
            self.summarize()

    def test_modified_calibration_source_is_rejected(self):
        (self.root/'vision/episodes_calibration/source.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'calibration input changed'):
            self.summarize()

    def test_inconsistent_success_horizon_is_rejected(self):
        self.row['duration_ms'] = 600
        self.row['log'][-1]['t_end_ms'] = 600
        write_json(self.episode, self.row)
        with self.assertRaisesRegex(ValueError, 'observation horizon'):
            self.summarize()


if __name__ == '__main__':
    unittest.main()
