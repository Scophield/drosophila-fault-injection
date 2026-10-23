"""Independent checks of cohort exclusion and common-exposure sensitivity."""
import sys
import unittest
from pathlib import Path

import numpy as np
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_assessment import (cohort_scores, exact_cluster_summary,
                              independent_median_effect, score, window_sensitivity)
from task_reference import reference


class Assessment(unittest.TestCase):
    def test_joint_rule_cannot_add_transmission_passes(self):
        rows = [dict(pop_rate=rate, n_total_spikes=spikes)
                for rate, spikes in [(50,10), (100,100), (100,1000), (250,10)]]
        self.assertEqual(score(rows,100,100), dict(n=4,transmission=3,joint=1,additional_rejections=2))

    def test_exclusion_is_done_on_records_not_pooled_medians(self):
        q = cohort_scores(ROOT/'sim/results/real', ROOT/'sim_vision/results_vision/openloop_controls')
        full = q['exclusions']['all_faults_controls']
        subset = q['exclusions']['excluding_all_targeted_hub_cohorts']
        main = q['exclusions']['main_F1_F2_F3_F5_only']
        self.assertEqual((full['n'],full['transmission'],full['joint']),(288,276,262))
        self.assertEqual((subset['n'],subset['transmission'],subset['joint']),(204,192,190))
        self.assertEqual((main['n'],main['transmission'],main['joint']),(180,168,168))
        self.assertEqual(q['healthy_resubstitution']['additional_rejections'],0)

    def test_reference_variation_enters_effect_interval(self):
        effect = independent_median_effect([dict(x=2)]*3,[dict(x=v) for v in [1,2,4]],'x')
        self.assertEqual(effect['ratio'],1)
        self.assertEqual(effect['ratio_ci95'],[.5,2.])

    def test_exact_cluster_support_and_window_sensitivity(self):
        exact = exact_cluster_summary([dict(seed=s,ratio=v) for s,v in enumerate([1.,2.,3.])])
        self.assertEqual(exact['ordered_resamples'],27)
        self.assertEqual(exact['distinct_statistics'],3)
        q = window_sensitivity(ROOT/'sim_vision/results_vision')
        for window in ('200','300','400','500'):
            self.assertEqual(q['F4_1pct'][window]['exceedances'],0)
            self.assertEqual(q['HUB_inh'][window]['exceedances'],12)
            self.assertEqual(len(q['F2_50'][window]['seed_medians']),3)
        self.assertAlmostEqual(q['F2_50']['400']['median'],.7226281760002999)

    def test_privileged_reference_is_horizon_limited_and_has_no_neural_model(self):
        with patch.dict(sys.modules, {'brian2':SimpleNamespace(seed=lambda _:None)}):
            short=reference(30,1000)
            long=reference(30,1200)
            mirrored=reference(-30,1000)
        self.assertTrue(short['escaped'])
        self.assertFalse(long['escaped'])
        self.assertAlmostEqual(short['min_dist'],mirrored['min_dist'])
        self.assertEqual(short['n_total'],0)
        self.assertFalse(short['neural_simulation'])


if __name__ == '__main__':
    unittest.main()
