"""Tiny Brian2 replay test; no connectome tables or full neural graph."""
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sim_vision'))
from task_v9 import input_uniforms


@unittest.skipUnless(importlib.util.find_spec('brian2'),'Brian2 is optional for pure analysis')
class InputReplay(unittest.TestCase):
    def test_actual_spike_generator_emits_exact_shared_uniform_schedule(self):
        import brian2 as b
        b.start_scope();b.defaultclock.dt=.1*b.ms;b.prefs.codegen.target='numpy'
        spec=importlib.util.spec_from_file_location('vision_v9_sampling_test',ROOT/'sim_vision/vision_v9.py')
        mod=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'vision_core':SimpleNamespace(VisionSim=object)}):
            spec.loader.exec_module(mod)
        obj=mod.PairedVisionSim.__new__(mod.PairedVisionSim)
        obj.pool_flyids=np.arange(3);obj.pool_pos={i:i for i in range(3)};obj.sens_flyids=np.arange(3)
        obj.input_seed=777;obj.input_frame=0;obj.uniform_hash=hashlib.sha256();obj.event_hash=hashlib.sha256()
        obj.stim=b.SpikeGeneratorGroup(3,[],[]*b.ms)
        mon=b.SpikeMonitor(obj.stim);net=b.Network(obj.stim,mon)
        rates=np.array([0.,150.,75.]);expected_i=[];expected_t=[]
        for frame in range(2):
            times,ids=np.nonzero(input_uniforms(777,frame,3)<rates[None,:]*.0001)
            expected_i.extend(ids);expected_t.extend(frame*20+times*.1)
            obj.set_frame_rates(rates);net.run(20*b.ms)
        np.testing.assert_array_equal(mon.i[:],expected_i)
        np.testing.assert_allclose(mon.t[:]/b.ms,expected_t,atol=1e-10)
        self.assertGreater(len(expected_i),0)
        self.assertEqual(obj.input_frame,2)


if __name__=='__main__':unittest.main()
