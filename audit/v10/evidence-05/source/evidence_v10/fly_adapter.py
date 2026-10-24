"""Adapt existing fly traces; reuse the separately implemented input/geometry replay.

The generic contract has no dependency on the fly task. This adapter reads its
schema, bindings and units; neither adapter nor replay runs neural equations.
"""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import numpy as np
from .contract import Evidence,Campaign
from tools.replay_audit_v9 import check_record


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class FlyAdapter:
    def __init__(self,root,calibration,registration):
        self.root=Path(root);self.cal_path=Path(calibration);self.reg_path=Path(registration)
        self.cal=json.loads(self.cal_path.read_text());self.reg=json.loads(self.reg_path.read_text())
        self.im_path=self.root/'input-map.json';self.im=json.loads(self.im_path.read_text())
        self.cal_sha=sha(self.cal_path);self.map_sha=sha(self.im_path)
        self.manifest_paths={sha(p):p for p in (self.root/'batches').glob('*/run_manifest.json')}
        self.manifests={h:json.loads(p.read_text()) for h,p in self.manifest_paths.items()}
        self.manifest_issues={h:self.check_manifest(m,self.manifest_paths[h]) for h,m in self.manifests.items()}
        self.spec=Campaign(tuple(self.reg['test_seeds']),tuple(self.reg['phis']),tuple(self.reg['modes']),
            tuple(self.reg['faults']),1.,.02,'network spikes')

    def check_manifest(self,m,path):
        """Bind generating snapshot bytes/entry points to the frozen registration."""
        errors=[];cfg=m['parameters'];frozen=self.reg['frozen_source_sha256']
        if cfg['role']!='test' or cfg['registration_sha256']!=sha(self.reg_path):errors.append('registration/role')
        if cfg['calibration_sha256']!=self.cal_sha or self.reg['calibration_sha256']!=self.cal_sha:errors.append('registered calibration')
        if m['annotations_sha256']!=self.reg['annotations_sha256']:errors.append('annotations')
        if m['model_inputs']!=self.reg['model_inputs_sha256']:errors.append('external model')
        if m['python']!=self.reg['runtime']['python'] or m['packages']!=self.reg['runtime']['packages']:errors.append('runtime declaration')
        simulation={n:h for n,h in m['source_sha256'].items() if n.startswith(('sim/','sim_vision/'))}
        expected={n:h for n,h in frozen.items() if n.startswith(('sim/','sim_vision/'))}
        if simulation!=expected:errors.append('registered simulation source set')
        digest=hashlib.sha256(''.join(f'{n}:{simulation[n]}\n' for n in sorted(simulation)).encode()).hexdigest()
        if digest!=m['code_sha256']:errors.append('composite source digest')
        for n,h in {**m['source_sha256'],**cfg['entrypoint_sha256']}.items():
            registered=self.reg['model_inputs_sha256']['model.py'] if n=='external/model.py' else frozen.get(n)
            if registered!=h:errors.append('unregistered generating source: '+n)
            p=path.parent/'source'/n
            if not p.is_file() or sha(p)!=h:errors.append('generating snapshot bytes: '+n)
        return errors

    def normalize(self,r):
        fail=None if r['collision_ms'] is None else r['collision_ms']/1000
        m=self.manifests.get(r['run_manifest_sha256'],{})
        bindings=dict(protocol=r['protocol'],map=r['input_map_sha256'],calibration=r['calibration_sha256'],
                      neural_sources=m.get('code_sha256'),model=m.get('model_inputs'),
                      configuration={k:v for k,v in m.get('parameters',{}).items() if k!='seeds'})
        frames=[dict(start_s=q['t_ms']/1000,end_s=q['t_end_ms']/1000,
                     decision_s=q['t_end_ms']/1000,usable_after_s=q['t_end_ms']/1000,resource=q['n_total']) for q in r['log']]
        return Evidence(r['seed'],r['phi_deg'],r['mode'],r['fault'],r['horizon_ms']/1000,.02,bindings,
            r['uniform_sha256'],r['mask_sha256'],r['deleted_rows'],frames,fail,r['escaped'],r)

    @lru_cache(maxsize=1)
    def streams(self,seed):
        us=[np.random.default_rng(np.random.SeedSequence([20261022,seed,k,1])).random((200,len(self.im['pool_flyids'])),dtype=np.float32) for k in range(50)]
        h=hashlib.sha256()
        for u in us:h.update(u.tobytes())
        return us,h.hexdigest()

    def check_native(self,e):
        r=e.native
        if any(not isinstance(q['n_total'],int) or isinstance(q['n_total'],bool) or q['n_total']<0 for q in r['log']):raise ValueError('network spikes must be nonnegative integer counts')
        if r['input_map_sha256']!=self.map_sha or r['calibration_sha256']!=self.cal_sha:raise ValueError('external input/calibration binding')
        if r['run_manifest_sha256'] not in self.manifests:raise ValueError('missing generating manifest')
        if self.manifest_issues[r['run_manifest_sha256']]:raise ValueError('manifest binding: '+repr(self.manifest_issues[r['run_manifest_sha256']]))
        m=self.manifests[r['run_manifest_sha256']]
        if m['model_inputs']!=self.reg['model_inputs_sha256']:raise ValueError('external model mismatch')
        us,h=self.streams(r['seed']);check_record(r,self.cal,self.im,us,h)

    def check_pair(self,group):
        if not group:return
        seed=group[0].cluster;n=group[0].native['n_connection_rows']
        u=np.random.default_rng(np.random.SeedSequence([20261022,seed,2])).random(n)
        expected={}
        prior=np.zeros(n,dtype=bool)
        for name,f in [('healthy',0.),('F2_25',.25),('F2_50',.5)]:
            mask=u<f
            if np.any(prior&~mask):raise ValueError('mask nesting')
            expected[name]=(hashlib.sha256(np.packbits(mask).tobytes()).hexdigest(),int(mask.sum()));prior=mask
        for r in group:
            if (r.mask_sha256,r.deleted)!=expected[r.fault]:raise ValueError('mask identity/count differs from seed stream')

    def load(self):
        return [self.normalize(json.loads(p.read_text())) for p in sorted((self.root/'episodes').glob('*.json'))]
