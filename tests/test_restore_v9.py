"""Exercise the production episode reset on a tiny real Brian2 network."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec('brian2'),'Brian2 required for simulator reset check')
class EpisodeReset(unittest.TestCase):
    def test_restores_state_fault_weights_monitor_and_external_weights(self):
        import brian2 as b
        b.start_scope();b.defaultclock.dt=.1*b.ms;b.prefs.codegen.target='numpy'
        fake_engine=SimpleNamespace(W_IN_V=.06875,N_BACKGROUND=0,get_type_ids=lambda:{})
        spec=importlib.util.spec_from_file_location('vision_core_reset_test',ROOT/'sim_vision/vision_core.py')
        module=importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{'engine':fake_engine}):spec.loader.exec_module(module)
        obj=module.VisionSim.__new__(module.VisionSim)
        neurons=b.NeuronGroup(2,'v : volt',threshold='v > 1*mV',reset='v=0*mV')
        recurrent=b.Synapses(neurons,neurons,'w : volt',on_pre='v += w')
        recurrent.connect(i=[0],j=[1]);recurrent.w=2*b.mV
        stimulus=b.SpikeGeneratorGroup(1,[0],[0]*b.ms)
        obj.syn_stim=b.Synapses(stimulus,neurons,'w : volt',on_pre='v += w')
        obj.syn_stim.connect(i=[0],j=[0]);obj.syn_stim.w=0*b.mV
        monitor=b.SpikeMonitor(neurons)
        obj.net=b.Network(neurons,recurrent,stimulus,obj.syn_stim,monitor)
        obj.net.store('init')
        obj._stim_w=np.array([.003])
        obj.reset_state();obj.net.run(1*b.ms)
        first=np.array(monitor.i[:]);self.assertGreater(len(first),0)
        recurrent.w=0*b.mV;neurons.v=9*b.mV
        obj.reset_state()
        self.assertEqual(float(obj.net.t/b.ms),0)
        self.assertEqual(len(monitor.i[:]),0)
        np.testing.assert_array_equal(np.asarray(neurons.v[:]/b.mV),[0,0])
        np.testing.assert_array_equal(np.asarray(recurrent.w[:]/b.mV),[2])
        np.testing.assert_allclose(obj.syn_stim.w[:]/b.volt,[.003])
        obj.net.run(1*b.ms)
        np.testing.assert_array_equal(monitor.i[:],first)


if __name__=='__main__':unittest.main()
