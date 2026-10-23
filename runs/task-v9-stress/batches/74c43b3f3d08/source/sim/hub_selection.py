"""Common contact-ranked hub definition, independent of Brian2 and graph targets."""
import hashlib
import json
from pathlib import Path

import numpy as np

SELECTOR_VERSION = 'contact-count-flyid-tiebreak-v1'


def mapped_ids(i2flyid, n):
    if set(i2flyid) != set(range(n)):
        raise ValueError('i2flyid must map every contiguous neuron index')
    ids = np.array([int(i2flyid[i]) for i in range(n)], dtype=np.int64)
    if len(np.unique(ids)) != n:
        raise ValueError('FlyIDs must be unique')
    return ids


def select_hubs(contact_counts, i2flyid, protected, n):
    scores = np.asarray(contact_counts)
    if scores.ndim != 1 or not np.all(np.isfinite(scores)) or np.any(scores < 0):
        raise ValueError('invalid contact counts')
    if not np.allclose(scores, np.rint(scores), atol=1e-5, rtol=0):
        raise ValueError('hub scores must be integer contact counts')
    ids = mapped_ids(i2flyid, len(scores))
    protected = {int(x) for x in protected}
    order = np.lexsort((ids, -np.rint(scores).astype(np.int64)))
    eligible = order[~np.isin(ids[order], list(protected))]
    if not 0 <= n <= len(eligible):
        raise ValueError('requested hub count exceeds eligible population')
    selected = eligible[:n].astype(np.int64)
    assert not (set(ids[selected]) & protected)
    return selected


def profile(sim, weight_scale=2.75e-4):
    if not hasattr(sim, '_hub_profile'):
        pre = np.asarray(sim._pre_idx, dtype=np.int64)
        contacts = np.abs(sim.w0) / weight_scale
        if not np.allclose(contacts, np.rint(contacts), atol=1e-4, rtol=0):
            raise ValueError('weights do not recover integer contact counts')
        counts = np.bincount(pre, weights=np.rint(contacts), minlength=sim.n_neurons).astype(np.int64)
        sign = np.zeros(sim.n_neurons, dtype=np.int8)
        _, first = np.unique(pre, return_index=True)
        sign[pre[first]] = np.sign(sim.w0[first]).astype(np.int8)
        sim._hub_profile = (counts, sign)
    return sim._hub_profile


def for_sim(sim, protected, fraction):
    counts, _ = profile(sim)
    return select_hubs(counts, sim.i2flyid, protected, int(round(fraction * sim.n_neurons)))


def manifest(sim, selected, protected):
    ids = mapped_ids(sim.i2flyid, sim.n_neurons)
    counts, signs = profile(sim)
    selected = np.asarray(selected, dtype=np.int64)
    flyids = sorted(int(x) for x in ids[selected])
    assert not (set(flyids) & set(protected))
    serialized = ''.join(f'{x}\n' for x in flyids).encode('ascii')
    edges = np.isin(sim._pre_idx, selected)
    return dict(selector=SELECTOR_VERSION, flyids=flyids,
                flyids_sha256=hashlib.sha256(serialized).hexdigest(),
                hash_encoding='sorted numeric FlyIDs, ASCII decimal, newline after each',
                protected_flyids=sorted(int(x) for x in protected), n_cells=len(flyids),
                n_inhibitory=int(np.sum(signs[selected] < 0)),
                n_excitatory=int(np.sum(signs[selected] > 0)),
                n_edges=int(edges.sum()), n_contacts=int(counts[selected].sum()),
                n_neurons=sim.n_neurons, n_total_edges=len(sim._pre_idx))


def save_manifest(path, sim, selected, protected):
    value = manifest(sim, selected, protected)
    path = Path(path)
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f'hub manifest changed: {path}')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2)+'\n')
    return value['flyids_sha256']
