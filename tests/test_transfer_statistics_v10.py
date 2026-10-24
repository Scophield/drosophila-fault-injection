"""Multiplicity-family and paired loss/gain regressions, with healthy failures."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tools')]
from aggregate_transfer_v10 import holm,primary


class TransferStatistics(unittest.TestCase):
    def test_global_family_is_not_within_map_adjustment(self):
        self.assertEqual(holm({'A/25':.5,'A/50':.001,'B/25':.2,'B/50':.01}),
                         {'A/50':.004,'B/50':.03,'B/25':.4,'A/25':.5})
    def test_ties_and_invalid_p_values(self):
        adjusted=holm({'a':.1,'b':.1,'c':1.})
        self.assertAlmostEqual(adjusted['a'],.3);self.assertAlmostEqual(adjusted['b'],.3)
        self.assertEqual(adjusted['c'],1.)
        for bad in [{}, {'a':float('nan')},{'a':-1}]:
            with self.assertRaises(ValueError):holm(bad)
    def test_fault_gains_are_not_hidden_when_healthy_fails(self):
        rows=[]
        for seed in [1,2]:
            for phi in [-30,30]:
                for fault in ['healthy','F2_25','F2_50']:
                    rows.append(dict(seed=seed,phi_deg=phi,mode='proportional',fault=fault,
                        escaped=(phi>0 if fault=='healthy' else phi<0)))
        reg=dict(test_seeds=[1,2],phis=[-30,30],modes=['proportional'],bootstrap=dict(seed=1,draws=100))
        q=primary(rows,reg)[0]['estimands']
        self.assertEqual(q['loss']['estimate'],.5);self.assertEqual(q['gain']['estimate'],.5)
        self.assertEqual(q['net_loss']['estimate'],0.)
        self.assertEqual(q['net_loss']['role'],'derived');self.assertEqual(q['loss']['role'],'registered_primary')
        self.assertEqual(q['loss']['unit'],'proportion');self.assertEqual(q['loss']['display_scale'],100)

    def test_zero_bootstrap_is_not_zero_population_risk(self):
        rows=[dict(seed=s,phi_deg=p,mode='proportional',fault=f,escaped=True)
              for s in [1,2] for p in [-30,30] for f in ['healthy','F2_25','F2_50']]
        reg=dict(test_seeds=[1,2],phis=[-30,30],modes=['proportional'],bootstrap=dict(seed=1,draws=100))
        q=primary(rows,reg)[0]['estimands']['loss']
        self.assertEqual(q['ci95'],[0.,0.])
        self.assertAlmostEqual(q['zero_event_any_cluster_upper95'],1-.05**.5)


if __name__=='__main__':unittest.main()
