"""Fixed, raw-record additional challenges; no checker is called here.

The case families/labels precede scoring in challenge-spec.json. This is an
additional author-designed evaluation, not blind generalization evidence.
"""
import copy
import hashlib
import json
import random


SEED = 2026102501
REPETITIONS = 3
SPEC_KEYS = ('clusters', 'conditions', 'laws', 'faults', 'horizon_s', 'frame_s')
VALID = ('unaltered', 'legal_nonframe_actuation', 'legal_worker_seed_partition',
         'legal_feedback_dependence')
INVALID = ('uniform_identity', 'mask_identity', 'seed_identity',
           'condition_identity', 'actuator_start', 'actuator_end',
           'endpoint_actuator_state', 'task_label_contradiction',
           'first_failure_time', 'resource_decrease',
           'monotone_resource_bias', 'truncated_exposure',
           'missing_required_header', 'uniform_binding_replacement')


class Unavailable(Exception):
    """A structural precondition is absent; preserve and report the case."""


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _changed_digest(value):
    # Preserve syntax and length: failure is identity rather than bad formatting.
    return ('1' if value[0] != '1' else '2') + value[1:]


def _key(plant, r):
    return [r['seed'], r['phi_deg'] if plant == 'fly' else r['condition'],
            r['mode'] if plant == 'fly' else r['law'], r['fault']]


def _event(rows, *, last=False):
    events = [(i, j) for i, q in enumerate(rows)
              for j, s in enumerate(q['segments']) if s['burst']]
    if not events:
        raise Unavailable('No observed burst-on segment in the selected row')
    return events[-1] if last else events[0]


def _split_tank_frame(rows):
    candidates = [i for i, q in enumerate(rows) if len(q['segments']) > 1]
    if not candidates:
        raise Unavailable('No observed internal actuator event in selected row')
    return candidates[0]


def _check_valid_precondition(family, plant, rows, spec):
    if family == 'legal_nonframe_actuation':
        if plant == 'fly':
            yes = any(s['burst'] and abs(s['start_ms']/20-round(s['start_ms']/20)) > 1e-9
                      for r in rows for q in r['log'] for s in q['segments'])
        else:
            yes = any(abs(q['available_s']/.1-round(q['available_s']/.1)) > 1e-9
                      for r in rows for q in r['log'])
        if not yes:
            raise Unavailable('Selected unaltered block has no off-frame event')
    if family == 'legal_feedback_dependence':
        pairs = {}
        for r in rows:
            context = (r['seed'], r['phi_deg'] if plant == 'fly' else r['condition'], r['fault'])
            if plant == 'fly':
                signature = r['event_sha256']
            else:
                signature = _digest([(q['level'], q['requested']) for q in r['log']])
            pairs.setdefault(context, []).append((r['uniform_sha256'], signature))
        yes = any(len({u for u, v in p}) == 1 and len({v for u, v in p}) > 1
                  for p in pairs.values())
        if not yes:
            raise Unavailable('No recorded law-dependent event/plant history in selected block')


def _worker_composite(plant, groups, index, rows, spec):
    """Combine genuine source blocks without adding a new RNG draw.

    Fly controls require two disjoint generating-manifest sets. Tank has no
    worker manifests, and therefore only tests a declared two-seed subset.
    This pre-execution amendment changes no other family or selection draw.
    """
    first = groups[index]
    first_seeds = set(first['clusters'])
    first_manifests = {r['run_manifest_sha256'] for r in first['records']} if plant == 'fly' else set()
    candidates = []
    for other_index, other in enumerate(groups):
        if other_index == index or other.get('adapter_key', plant) != first.get('adapter_key', plant):
            continue
        if first_seeds.intersection(other['clusters']):
            continue
        if any(other[k] != first[k] for k in SPEC_KEYS if k != 'clusters'):
            continue
        manifests = {r['run_manifest_sha256'] for r in other['records']} if plant == 'fly' else set()
        if plant == 'fly' and (not first_manifests or not manifests or not first_manifests.isdisjoint(manifests)):
            continue
        candidates.append((tuple(sorted(other['clusters'])), other_index, other, manifests))
    if not candidates:
        raise Unavailable('No same-adapter different-seed block with distinct real worker manifests' if plant == 'fly'
                          else 'No same-adapter different-seed block for declared subcampaign')
    _, other_index, other, manifests = min(candidates, key=lambda item: (item[0], item[1]))
    rows.extend(copy.deepcopy(other['records']))
    spec['clusters'] = tuple(first['clusters'])+tuple(other['clusters'])
    return dict(additional_base_group_index=other_index,
                source_group_digests=[_digest(first['records']), _digest(other['records'])],
                worker_evidence='two distinct real generating worker manifests' if plant == 'fly'
                                else 'declared two-seed subcampaign only; tank has no worker manifests',
                first_worker_manifests=sorted(first_manifests), second_worker_manifests=sorted(manifests))


def _mutate(family, plant, rows, index, rng, changes):
    r = rows[index]
    def set_value(obj, field, value, path):
        before = copy.deepcopy(obj[field])
        obj[field] = value
        changes.append(dict(path=path, before=before, after=copy.deepcopy(value)))
    prefix = f'records/{index}'
    if family in ('uniform_identity', 'mask_identity'):
        field = 'uniform_sha256' if family == 'uniform_identity' else 'mask_sha256'
        set_value(r, field, _changed_digest(r[field]), prefix+'/'+field)
    elif family == 'seed_identity':
        set_value(r, 'seed', r['seed']+1000000, prefix+'/seed')
    elif family == 'condition_identity':
        field = 'phi_deg' if plant == 'fly' else 'condition'
        value = -r[field] if plant == 'fly' else ('low' if r[field] == 'high' else 'high')
        set_value(r, field, value, prefix+'/'+field)
    elif family == 'actuator_start':
        if plant == 'fly':
            i, j = _event(r['log']); segments = r['log'][i]['segments']
            onset = segments[j]['start_ms']; new_onset = onset+1.
            if not new_onset < segments[j]['end_ms']:
                raise Unavailable('First burst-on segment is shorter than the fixed 1-ms shift')
            if j:
                set_value(segments[j-1], 'end_ms', new_onset, f'{prefix}/log/{i}/segments/{j-1}/end_ms')
                set_value(segments[j], 'start_ms', new_onset, f'{prefix}/log/{i}/segments/{j}/start_ms')
            else:
                off = copy.deepcopy(segments[0]); off.update(start_ms=onset, end_ms=new_onset, burst=False)
                set_value(segments[0], 'start_ms', new_onset, f'{prefix}/log/{i}/segments/0/start_ms')
                segments.insert(0, off)
                changes.append(dict(path=f'{prefix}/log/{i}/segments', operation='prepend 1-ms walk segment at original burst onset'))
        else:
            i = rng.randrange(len(r['log']))
            set_value(r['log'][i], 'available_s', r['log'][i]['available_s']+.01, f'{prefix}/log/{i}/available_s')
    elif family == 'actuator_end':
        if plant == 'fly':
            i, j = _event(r['log'], last=True); segments = r['log'][i]['segments']
            end = segments[j]['end_ms']; new_end = end-1.
            if not segments[j]['start_ms'] < new_end:
                raise Unavailable('Last burst-on segment shorter than fixed 1-ms shift')
            off = copy.deepcopy(segments[j]); off.update(start_ms=new_end, end_ms=end, burst=False)
            set_value(segments[j], 'end_ms', new_end, f'{prefix}/log/{i}/segments/{j}/end_ms')
            segments.insert(j+1, off)
            changes.append(dict(path=f'{prefix}/log/{i}/segments', operation='append 1-ms walk-marked segment after shortened burst'))
        else:
            i = _split_tank_frame(r['log']); segments = r['log'][i]['segments']
            boundary = segments[0]['end_s']+.01
            if not segments[0]['start_s'] < boundary < segments[1]['end_s']:
                raise Unavailable('No room for fixed 0.01-s internal boundary shift')
            set_value(segments[0], 'end_s', boundary, f'{prefix}/log/{i}/segments/0/end_s')
            set_value(segments[1], 'start_s', boundary, f'{prefix}/log/{i}/segments/1/start_s')
    elif family == 'endpoint_actuator_state':
        if plant == 'fly':
            set_value(r, 'burst_active_at_horizon', not r['burst_active_at_horizon'], prefix+'/burst_active_at_horizon')
        else:
            i = _split_tank_frame(r['log']); segments = r['log'][i]['segments']
            merged = copy.deepcopy(segments[0]); merged.update(end_s=segments[-1]['end_s'], final=segments[-1]['final'])
            changes.append(dict(path=f'{prefix}/log/{i}/segments', operation='merge applied-control event partition', before=len(segments), after=1))
            r['log'][i]['segments'] = [merged]
    elif family == 'task_label_contradiction':
        field = 'escaped' if plant == 'fly' else 'success'
        set_value(r, field, not r[field], prefix+'/'+field)
    elif family == 'first_failure_time':
        field, success = ('collision_ms', 'escaped') if plant == 'fly' else ('failure_s', 'success')
        horizon, step = (r['horizon_ms'], .5) if plant == 'fly' else (r['config']['horizon_s'], .005)
        old = r[field]
        value = horizon-step if old is None else old+step if old+step < horizon else old-step
        set_value(r, field, value, prefix+'/'+field)
        set_value(r, success, False, prefix+'/'+success)
    elif family == 'resource_decrease':
        field = 'n_total' if plant == 'fly' else 'resource'
        eligible = [i for i in range(1, len(r['log'])) if r['log'][i-1][field] >= 1]
        if not eligible:
            raise Unavailable('Selected row has no positive predecessor resource counter')
        i = rng.choice(eligible)
        set_value(r['log'][i], field, r['log'][i-1][field]-1, f'{prefix}/log/{i}/{field}')
    elif family == 'monotone_resource_bias':
        field = 'n_total' if plant == 'fly' else 'resource'
        for i, q in enumerate(r['log']):
            set_value(q, field, q[field]+10, f'{prefix}/log/{i}/{field}')
        if plant == 'fly':
            set_value(r, 'n_total', r['n_total']+10, prefix+'/n_total')
    elif family == 'truncated_exposure':
        changes.append(dict(path=prefix+'/log', operation='remove last observation frame', before=len(r['log']), after=len(r['log'])-1))
        r['log'].pop()
    elif family == 'missing_required_header':
        changes.append(dict(path=prefix+'/mask_sha256', operation='delete', before=r.pop('mask_sha256')))
    elif family == 'uniform_binding_replacement':
        field = 'input_map_sha256' if plant == 'fly' else 'source_sha256'
        replacement = _changed_digest(rows[0][field])
        for i, row in enumerate(rows):
            set_value(row, field, replacement, f'records/{i}/{field}')
    elif family == 'declared_burst_header':
        set_value(r, 'burst_delay_ms', r['burst_delay_ms']+10., prefix+'/burst_delay_ms')
        set_value(r, 'burst_duration_ms', r['burst_duration_ms']+10., prefix+'/burst_duration_ms')
    else:
        raise ValueError(family)


def build_cases(fly_groups, tank_groups, seed=SEED):
    """Build 111 pre-labelled cases, without importing or calling a checker.

    Each family draws three distinct source blocks via the fixed RNG, then
    draws its target row without looking at task outcomes. Repetitions are
    software challenge instances, not independent neural samples.
    """
    rng = random.Random(seed); cases = []
    for plant, groups in [('fly', fly_groups), ('tank', tank_groups)]:
        if len(groups) < REPETITIONS:
            raise ValueError('At least three source blocks per plant are required')
        families = VALID+INVALID+(('declared_burst_header',) if plant == 'fly' else ())
        for family in families:
            order = list(range(len(groups))); rng.shuffle(order)
            for repetition, group_index in enumerate(order[:REPETITIONS], 1):
                group = groups[group_index]
                rows = copy.deepcopy(group['records'])
                spec = {k: copy.deepcopy(group[k]) for k in SPEC_KEYS}
                target = rng.randrange(len(rows)); source_key = _key(plant, rows[target])
                changes = []; applicable = True; reason = None; extra = {}
                try:
                    if family in VALID:
                        if family == 'legal_worker_seed_partition':
                            extra = _worker_composite(plant, groups, group_index, rows, spec)
                        _check_valid_precondition(family, plant, rows, spec)
                    else:
                        _mutate(family, plant, rows, target, rng, changes)
                except Unavailable as error:
                    applicable = False; reason = str(error)
                cases.append(dict(id=f'{plant}:{family}:{repetition:02d}', plant=plant,
                    adapter_key=group.get('adapter_key', plant), family=family,
                    expected_invalid=family not in VALID, base_group_index=group_index,
                    repetition=repetition, target_record_index=target,
                    original_target_key=source_key, source_group_digest=_digest(rows) if family == 'legal_worker_seed_partition' else _digest(group['records']),
                    records=rows, spec=spec, applicable=applicable,
                    applicability_reason=reason, mutation=changes or [dict(operation='unaltered source records', purpose=family)],
                    evaluation_scope='fixed additional challenge; not blind/general coverage', **extra))
    assert len(cases) == 111
    return cases
