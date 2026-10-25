"""Exact-count warning boundary tests and frozen-cohort regression checks.

The oracle below uses integer spike totals and rational order-statistic weights,
independently of the warning implementation. Validation records alone determine
cutoffs; test labels enter only the final, separately computed confusion counts.
No neural dynamics or frozen-file writes are performed.
"""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import copy
import hashlib
import json
import math
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'sim_vision')]
import task_metrics_v9 as metrics


CONFIGS={
    'RF-0': ('runs/task-v9-frozen/registration-core.json','audit/acceptance-v9/core-v2/summary.json'),
    'RF-A': ('runs/task-v10-transfer/map-A/registration.json','audit/v10/transfer-01/map-A/analysis/summary.json'),
    'RF-B': ('runs/task-v10-transfer/map-B/registration.json','audit/v10/transfer-01/map-B/analysis/summary.json'),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def source_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def integer_oracle(record):
    """Saved rates are counts/0.020 s: use exact division on the 50-Hz lattice."""
    rows=[q for q in record['log'] if 100<q['t_end_ms']<=400]
    assert len(rows)==15
    total=0
    for q in rows:
        assert len(q['cmd_rates'])==8
        for rate in q['cmd_rates']:
            value=Fraction(rate)/50
            assert value.denominator==1 and value>=0
            total+=value.numerator
    return total


def fifth_percentile_oracle(records):
    values=sorted(integer_oracle(r) for r in records if r['fault']=='healthy')
    assert values
    # Linear/type-7 fifth percentile. Weights come from the rational rank,
    # rather than a floating percentile on already rounded rates.
    rank=Fraction(len(values)-1,20)
    lower=rank.numerator//rank.denominator
    upper=min(lower+1,len(values)-1)
    return values[lower]*(1-(rank-lower))+values[upper]*(rank-lower)


def own_confusion(records,flags):
    result=Counter(tp=0,fp=0,tn=0,fn=0)
    for r,predicted in zip(records,flags):
        positive=not r['escaped']
        result['tp' if positive and predicted else 'fn' if positive else 'fp' if predicted else 'tn']+=1
    return dict(result)


def native_fixture(count=14):
    log=[]
    for end in range(20,1001,20):
        log.append(dict(t_ms=end-20,t_end_ms=end,cmd_rates=[0.]*8))
    positions=[(q,j) for q in log if 100<q['t_end_ms']<=400 for j in range(8)]
    for i in range(count):
        q,j=positions[i%len(positions)];q['cmd_rates'][j]+=50.
    return dict(log=log,fault='healthy')


def cutoff(value):
    value=Fraction(value)
    return dict(numerator=value.numerator,denominator=value.denominator,
                comparison='<',equality='not flagged')


class CountAndBoundaryTests(unittest.TestCase):
    def test_lossless_count_and_exact_window_endpoints(self):
        record=native_fixture(14)
        next(q for q in record['log'] if q['t_end_ms']==100)['cmd_rates']=[500000.]*8
        next(q for q in record['log'] if q['t_end_ms']==420)['cmd_rates']=[500000.]*8
        self.assertEqual(metrics.command_count(record),14)
        self.assertEqual(metrics.command_count(native_fixture(0)),0)
        self.assertEqual(metrics.command_count(native_fixture(121)),121)

    def test_exact_tie_and_adjacent_integer_decisions(self):
        for boundary in [Fraction(14),Fraction(291,20),Fraction(271,20)]:
            lo=boundary.numerator//boundary.denominator
            for count in [max(0,lo-1),lo,lo+1,lo+2]:
                self.assertEqual(metrics.command_alert(count,cutoff(boundary)),Fraction(count)<boundary)
        self.assertTrue(metrics.command_alert(13,cutoff(14)))
        self.assertFalse(metrics.command_alert(14,cutoff(14)))
        self.assertFalse(metrics.command_alert(15,cutoff(14)))

    def test_linear_order_statistic_weights_are_exact_and_order_invariant(self):
        # For n=32, h=31/20: 45% of count 14 plus 55% of count 15.
        values=[0,14,15]+[100]*29
        self.assertEqual(metrics.linear_count_quantile(values),Fraction(291,20))
        self.assertEqual(metrics.linear_count_quantile(list(reversed(values))),Fraction(291,20))
        self.assertEqual(metrics.linear_count_quantile([0,10],Fraction(1,4)),Fraction(5,2))
        self.assertEqual(metrics.linear_count_quantile([9]),Fraction(9))

    def test_no_rounding_of_off_lattice_or_nonfinite_rates(self):
        invalid=[-50.,50.1,np.nextafter(50.,100.),float('nan'),float('inf'),
                 np.nextafter(np.float32(50.),np.float32(100.))]
        for value in invalid:
            with self.subTest(value=value):
                record=native_fixture();record['log'][5]['cmd_rates'][0]=value
                with self.assertRaises(ValueError):metrics.command_count(record)

    def test_missing_duplicate_unordered_or_wrong_duration_bins_rejected(self):
        records=[]
        r=native_fixture();del r['log'][8];records.append(r)
        r=native_fixture();r['log'].insert(8,copy.deepcopy(r['log'][8]));records.append(r)
        r=native_fixture();r['log'][8],r['log'][9]=r['log'][9],r['log'][8];records.append(r)
        r=native_fixture();r['log'][8]['t_ms']-=1;records.append(r)
        r=native_fixture();r['log'][8]['cmd_rates']=r['log'][8]['cmd_rates'][:7];records.append(r)
        for record in records:
            with self.assertRaises(ValueError):metrics.command_count(record)

    def test_incomplete_or_invalid_window_rejected(self):
        for t in [100,99,401,410,float('nan'),float('inf')]:
            with self.subTest(t=t),self.assertRaises(ValueError):metrics.command_count(native_fixture(),t)

    def test_invalid_count_quantile_and_boundary_semantics_rejected(self):
        for counts in [[],[-1,1],[1,1.5],[True,2]]:
            with self.assertRaises(ValueError):metrics.linear_count_quantile(counts)
        for probability in [Fraction(-1,20),Fraction(21,20)]:
            with self.assertRaises(ValueError):metrics.linear_count_quantile([1,2],probability)
        for count in [-1,14.,True]:
            with self.assertRaises(ValueError):metrics.command_alert(count,cutoff(14))
        for bad in [dict(cutoff(14),comparison='<='),dict(cutoff(14),equality='flagged'),
                    dict(cutoff(14),denominator=0),dict(cutoff(14),denominator=-1)]:
            with self.assertRaises(ValueError):metrics.command_alert(14,bad)


class FrozenCohortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cohorts={}
        for rf,(registration_path,summary_path) in CONFIGS.items():
            registration=read(ROOT/registration_path);summary=read(ROOT/summary_path)
            validation=[];records=[]
            for name,expected in sorted(registration['validation_input_sha256'].items()):
                path=ROOT/name
                assert source_digest(path)==expected
                validation.append(read(path))
            for name,expected in sorted(summary['raw_input_sha256'].items()):
                path=ROOT/name
                assert source_digest(path)==expected
                records.append(read(path))
            cls.cohorts[rf]=dict(registration=registration,validation=validation,records=records)

    def test_healthy_validation_alone_recovers_all_three_exact_cutoffs(self):
        expected={'RF-0':Fraction(14),'RF-A':Fraction(291,20),'RF-B':Fraction(271,20)}
        for rf,c in self.cohorts.items():
            with self.subTest(RF=rf):
                self.assertEqual(len(c['validation']),32)
                self.assertTrue(all(r['fault']=='healthy' for r in c['validation']))
                self.assertFalse({r['seed'] for r in c['validation']} & {r['seed'] for r in c['records']})
                own=fifth_percentile_oracle(c['validation'])
                derived=metrics.count_cutoff(c['validation'])
                self.assertEqual(Fraction(derived['numerator'],derived['denominator']),own)
                self.assertEqual(own,expected[rf])
                self.assertEqual(derived['quantile'],'linear/type-7')
                self.assertEqual(derived['comparison'],'<')
                self.assertEqual(derived['equality'],'not flagged')

    def test_validation_failures_and_fault_outcomes_do_not_select_cutoffs(self):
        for rf,c in self.cohorts.items():
            with self.subTest(RF=rf):
                healthy=copy.deepcopy(c['validation'])
                for r in healthy:r['escaped']=False
                expected=metrics.count_cutoff(c['validation'])
                self.assertEqual(metrics.count_cutoff(healthy),expected)
                irrelevant=native_fixture(10000);irrelevant['fault']='F2_50';irrelevant['escaped']=False
                self.assertEqual(metrics.count_cutoff(healthy+[irrelevant]),expected)

    def test_frozen_hz_binding_preserves_registered_fields(self):
        for rf,c in self.cohorts.items():
            original=copy.deepcopy(c['registration']['thresholds'])
            bound=metrics.bind_count_cutoff(original,c['validation'])
            self.assertEqual(original,c['registration']['thresholds'])
            self.assertEqual({k:v for k,v in bound.items() if k!='command_count_cutoff'},original)
            own=fifth_percentile_oracle(c['validation'])
            self.assertEqual(Fraction(bound['command_count_cutoff']['numerator'],bound['command_count_cutoff']['denominator']),own)

    def test_frozen_hz_compatibility_accepts_four_ulps_not_five(self):
        for rf,c in self.cohorts.items():
            own=fifth_percentile_oracle(c['validation'])
            exact_hz=float(own/Fraction(12,5))
            for direction in [float('-inf'),float('inf')]:
                value=exact_hz
                for i in range(5):
                    value=math.nextafter(value,direction)
                    original=copy.deepcopy(c['registration']['thresholds']);original['command_lower_hz']=value
                    if i<4:
                        metrics.bind_count_cutoff(original,c['validation'])
                    else:
                        with self.assertRaises(ValueError):metrics.bind_count_cutoff(original,c['validation'])

    def test_nonfinite_or_negative_frozen_hz_rejected(self):
        c=self.cohorts['RF-0']
        for value in [float('nan'),float('inf'),float('-inf'),-1.]:
            threshold=copy.deepcopy(c['registration']['thresholds']);threshold['command_lower_hz']=value
            with self.subTest(value=value),self.assertRaises(ValueError):
                metrics.bind_count_cutoff(threshold,c['validation'])

    def test_flags_require_explicit_validation_binding(self):
        for rf,c in self.cohorts.items():
            with self.subTest(RF=rf),self.assertRaisesRegex(ValueError,'Bind.*validation'):
                metrics.flags(c['records'][0],c['registration']['thresholds'])

    def test_all_cohort_counts_and_flags_match_independent_integer_oracle(self):
        anchors={'RF-0':dict(tp=2,fp=51,tn=224,fn=11),'RF-A':dict(tp=2,fp=42,tn=99,fn=1),'RF-B':dict(tp=0,fp=24,tn=119,fn=1)}
        for rf,c in self.cohorts.items():
            own=fifth_percentile_oracle(c['validation'])
            bound=metrics.bind_count_cutoff(c['registration']['thresholds'],c['validation'])
            actual=[];expected=[]
            for record in c['records']:
                count=integer_oracle(record)
                self.assertEqual(metrics.command_count(record),count)
                expected.append(Fraction(count)<own)
                actual.append(metrics.flags(record,bound)['transmission'])
            self.assertEqual(actual,expected)
            self.assertEqual(own_confusion(c['records'],actual),anchors[rf])

    def test_nineteen_rf0_boundary_records_expose_historical_algebra_ambiguity(self):
        c=self.cohorts['RF-0'];threshold=c['registration']['thresholds']['command_lower_hz']
        own=fifth_percentile_oracle(c['validation']);self.assertEqual(own,Fraction(14))
        bound=metrics.bind_count_cutoff(c['registration']['thresholds'],c['validation'])
        old=[];alternative=[];affected=[]
        for record in c['records']:
            rows=[q for q in record['log'] if 100<q['t_end_ms']<=400]
            a=sum(sum(q['cmd_rates'])*.02 for q in rows)/(8*.3)
            b=sum(sum(q['cmd_rates']) for q in rows)/(8*15)
            old.append(a<threshold);alternative.append(b<threshold)
            if (a<threshold)!=(b<threshold):
                affected.append(record)
                self.assertEqual(integer_oracle(record),14)
                self.assertTrue(record['escaped'])
                self.assertFalse(metrics.flags(record,bound)['transmission'])
                self.assertEqual(Fraction(700,120),Fraction(14)/Fraction(12,5))
        self.assertEqual(len(affected),19)
        self.assertEqual(own_confusion(c['records'],old),dict(tp=2,fp=51,tn=224,fn=11))
        self.assertEqual(own_confusion(c['records'],alternative),dict(tp=2,fp=70,tn=205,fn=11))

    def test_float32_float64_and_cell_sum_orders_preserve_integer_decisions(self):
        for rf,c in self.cohorts.items():
            own=fifth_percentile_oracle(c['validation'])
            bound=metrics.bind_count_cutoff(c['registration']['thresholds'],c['validation'])['command_count_cutoff']
            for original in c['records']:
                count=integer_oracle(original);answer=Fraction(count)<own
                for dtype in [np.float32,np.float64]:
                    record=copy.deepcopy(original)
                    for q in record['log']:
                        q['cmd_rates']=[dtype(v) for v in reversed(q['cmd_rates'])]
                    converted=metrics.command_count(record)
                    self.assertEqual(converted,count)
                    self.assertEqual(metrics.command_alert(converted,bound),answer)
                    rates=np.array([v for q in record['log'] if 100<q['t_end_ms']<=400 for v in q['cmd_rates']],dtype=dtype)
                    # Summing exact 50-Hz lattice values then dividing by 50
                    # has an unambiguous integer meaning in either precision.
                    self.assertEqual(int(np.sum(rates,dtype=dtype)/dtype(50)),count)
                    self.assertEqual(int(np.sum(rates[::-1],dtype=dtype)/dtype(50)),count)

    def test_boundary_display_rate_cannot_replace_exact_flag(self):
        c=self.cohorts['RF-0'];bound=metrics.bind_count_cutoff(c['registration']['thresholds'],c['validation'])
        record=next(r for r in c['records'] if integer_oracle(r)==14)
        f=metrics.features(record)
        self.assertEqual(f['command_count'],14)
        self.assertEqual(f['command_hz'],float(Fraction(35,6)))
        self.assertLess(f['command_hz'],bound['command_lower_hz'])
        self.assertFalse(metrics.flags(record,bound)['transmission'])

    def test_future_activity_outcome_and_post400_rate_changes_cannot_change_count(self):
        for rf,c in self.cohorts.items():
            original=c['records'][0];record=copy.deepcopy(original)
            record['escaped']=not record['escaped'];record['collision_ms']=987.
            for q in record['log']:
                if q['t_end_ms']>400:
                    q['cmd_rates']=[float('nan')]*8;q['n_total']=10**12
            self.assertEqual(metrics.command_count(record),integer_oracle(original))


if __name__=='__main__':
    unittest.main()
