"""Lightweight regression checks: synthetic neurons and immutable archived records."""
import ast
import importlib.util
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace, ModuleType
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sim'))
sys.path.insert(0,str(ROOT/'tools'))
from hub_selection import select_hubs, for_sim, manifest, profile
from audit_archive import load, summarize, protocols, paired_episodes
from run_provenance import prepare, run_root
from check_reproduction import check_commands


def function(path,name,namespace):
    tree=ast.parse((ROOT/path).read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    return namespace[name]


class Hubs(unittest.TestCase):
    def setUp(self):
        self.sim=SimpleNamespace(n_neurons=200,i2flyid={i:100000+199-i for i in range(200)})
        self.sim._pre_idx=np.array([0,4,7,12,13,14])
        self.sim.w0=np.array([500,100,-100,20,-15,10])*2.75e-4
        self.sim.out_mask=lambda ids:np.isin(self.sim._pre_idx,ids)
        self.protected={self.sim.i2flyid[0]}

    def test_protected_uses_flyid_and_ties_use_identity(self):
        selected=for_sim(self.sim,self.protected,.01)
        self.assertEqual(selected.tolist(),[7,4])
        self.assertFalse(set(self.sim.i2flyid[i] for i in selected)&self.protected)

    def test_ties_survive_reindexing(self):
        scores=np.array([5,5,5,1]); ids={0:9003,1:9001,2:9002,3:9004}
        a=select_hubs(scores,ids,set(),2)
        perm=np.array([2,0,3,1]); b=select_hubs(scores[perm],{i:ids[int(j)] for i,j in enumerate(perm)},set(),2)
        self.assertEqual([ids[int(i)] for i in a],[ids[int(perm[i])] for i in b])

    def test_all_experiment_paths_agree(self):
        ns=dict(np=np,for_sim=for_sim)
        sweep=function('sim/sweep.py','apply_fault',ns)
        ids={'LC4':list(self.protected),'LPLC2':[],'DNp01':[],'DNa02':[],'DNp04':[],'DNb01':[]}
        engine=ModuleType('engine');engine.get_type_ids=lambda:ids
        closed=function('sim_vision/run_closedloop.py','build_fault',dict(np=np,for_sim=for_sim,profile=profile))
        rng=np.random.default_rng(0)
        w1=sweep(self.sim,dict(type='hub',frac=.01),list(self.protected),[],rng)
        with patch.dict(sys.modules,engine=engine):
            w2=closed(self.sim,'F4_1pct',rng)
        np.testing.assert_array_equal(w1,w2)
        tree=ast.parse((ROOT/'sim_vision/controls_openloop.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Setup')
        meth=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_top_cells')
        env=dict(select_hubs=select_hubs);exec(compile(ast.Module(body=[meth],type_ignores=[]),'controls','exec'),env)
        selected=env['_top_cells'](SimpleNamespace(sim=self.sim,out_deg=profile(self.sim)[0],protected=self.protected),2)
        np.testing.assert_array_equal(selected,for_sim(self.sim,self.protected,.01))

    def test_target_permutation_preserves_selection_and_damage(self):
        a=manifest(self.sim,for_sim(self.sim,self.protected,.01),self.protected)
        self.sim._post_idx=np.array([9,2,7,1,7,7])
        b=manifest(self.sim,for_sim(self.sim,self.protected,.01),self.protected)
        self.assertEqual(a,b)
        self.assertEqual(a['n_inhibitory'],1)
        self.assertEqual(a['n_edges'],2)

    def test_invalid_mapping_fails(self):
        with self.assertRaises(ValueError):
            select_hubs([1,2],{0:10,2:11},set(),1)


class Archive(unittest.TestCase):
    def test_protocol_tail(self):
        core=ROOT/'sim/results/real';ctrl=ROOT/'sim_vision/results_vision/openloop_controls'
        result=protocols(core,ctrl,summarize(load(core/'healthy.jsonl')))
        self.assertEqual((result['trials'],result['transmission_only_pass'],result['envelope_pass']),(288,276,262))
        failures={c['name']:[r['trial'] for r in c['additional_failures']] for c in result['conditions'] if c['additional_failures']}
        self.assertEqual(failures,dict(HUB_inh=list(range(12)),INHrand_mass=[3,9]))

    def test_paired_activity_and_escape(self):
        result=paired_episodes(ROOT/'sim_vision/results_vision')
        f=result['v4/F4_1pct'];h=result['v4c/HUB_inh']
        self.assertEqual((f['escaped'],f['activity_exceedances']),(12,6))
        self.assertTrue(all(p['ratio']>2 for p in f['pairs'] if p['phi']<0))
        self.assertEqual((h['escaped'],h['bursts'],h['activity_exceedances']),(6,12,12))

    def test_low_drive_scope(self):
        rows=load(ROOT/'sim_vision/results_vision/openloop_controls/F2_50_d75.jsonl')
        self.assertEqual(sum(r['pop_rate']>=51.4 for r in rows),10)

    def test_incomplete_closedloop_is_rejected(self):
        with self.assertRaises(ValueError):
            paired_episodes(ROOT/'does-not-exist')


class Outputs(unittest.TestCase):
    def test_archive_guard(self):
        with patch.dict(os.environ,FLY_RUN_DIR=str(ROOT/'sim/results/new')):
            with self.assertRaises(ValueError):run_root()

    def test_manifest_resume_does_not_mix_parameters(self):
        base=ROOT/'tmp'
        base.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as tmp, patch.dict(os.environ,FLY_RUN_DIR=tmp):
            out=Path(tmp)/'test'
            prepare(out,dict(seed=2))
            prepare(out,dict(seed=2),resume=True)
            with self.assertRaises(ValueError):prepare(out,dict(seed=3),resume=True)
            with self.assertRaises(ValueError):prepare(out,dict(seed=2))
            manifest=json.loads((out/'run_manifest.json').read_text())
            self.assertIn('source_sha256',manifest)
            for name,expected in manifest['source_sha256'].items():
                self.assertEqual(hashlib.sha256((out/'source'/name).read_bytes()).hexdigest(),expected)
            (out/'source/sim/run_provenance.py').write_text('changed snapshot')
            with self.assertRaises(ValueError):prepare(out,dict(seed=2),resume=True)

    def test_all_python_sources_parse(self):
        for folder in ('sim','sim_vision','tools','tests'):
            for p in (ROOT/folder).glob('*.py'):
                ast.parse(p.read_text(encoding='utf-8'),filename=str(p))

    def test_documented_command_flags(self):
        self.assertGreaterEqual(len(check_commands()),20)


if __name__=='__main__':unittest.main()
