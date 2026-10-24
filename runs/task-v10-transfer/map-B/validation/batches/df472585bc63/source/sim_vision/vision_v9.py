"""Same neural equations; frame-indexed shared uniforms replace global RNG."""
import numpy as np
from brian2 import SpikeGeneratorGroup, SpikeMonitor, Synapses, ms, volt
from vision_core import VisionSim
from task_v9 import input_uniforms


class PairedVisionSim(VisionSim):
    def __init__(self, command_flyids):
        super().__init__()
        self.net.remove(self.stim,self.syn_stim,self.mon_ro)
        self.stim=SpikeGeneratorGroup(len(self.pool_flyids),[],[]*ms,name='paired_input')
        self.syn_stim=Synapses(self.stim,self.neu,'w : volt',on_pre='v += w',delay=0*ms,name='paired_syn')
        self.syn_stim.connect(i=np.arange(len(self.pool_flyids)),j=self.pool_idx)
        self.syn_stim.w=0*volt
        indices=[self.flyid2i[int(f)] for f in command_flyids]
        self.mon_ro=SpikeMonitor(self.neu,record=indices)
        self.net.add(self.stim,self.syn_stim,self.mon_ro)
        self.net.store('init')

    def set_frame_rates(self,rates):
        base=np.zeros(len(self.pool_flyids))
        pos=[self.pool_pos[int(f)] for f in self.sens_flyids]
        base[pos]=rates
        u=input_uniforms(self.input_seed,self.input_frame,len(base))
        self.uniform_hash.update(u.tobytes())
        times,indices=np.nonzero(u < base[None,:]*.0001)
        absolute=self.input_frame*20+times*.1
        self.event_hash.update(np.column_stack([times,indices]).astype('<i4').tobytes())
        self.stim.set_spikes(indices,absolute*ms,sorted=True)
        self.input_frame+=1
