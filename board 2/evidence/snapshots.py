# -*- coding: utf-8 -*-
"""最小的 evidence snapshot persistence。

只做三件事：算 fingerprint、依 checkpoint 存檔、維護一份索引。
**不存任何 render 結果（HTML / Markdown）——那是 view，不是 domain object。**
"""
import hashlib, json, os, shutil

INDEX = 'snapshots.json'


def fingerprint(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def _index_path(sprint_dir):
    return os.path.join(sprint_dir, INDEX)


def load_index(sprint_dir):
    p = _index_path(sprint_dir)
    if not os.path.exists(p):
        return {'schema': 'evidence-snapshot-index/1.0', 'snapshots': []}
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def record(sprint_dir, evidence_path, lifecycle_state, taken_at):
    """把當前 evidence 存成該 checkpoint 的快照，並登記索引。

    同一個 lifecycle_state 重複 refresh：**覆蓋 payload，但保留第一次的 first_taken_at**，
    因為「T-2 當時看到什麼」以最後一次 refresh 為準，而「何時第一次進入這個狀態」要留著。
    """
    os.makedirs(sprint_dir, exist_ok=True)
    fp = fingerprint(evidence_path)
    snap_name = 'evidence-%s.json' % lifecycle_state.lower().replace('_', '-')
    dest = os.path.join(sprint_dir, snap_name)
    shutil.copyfile(evidence_path, dest)

    idx = load_index(sprint_dir)
    existing = next((s for s in idx['snapshots']
                     if s['lifecycle_state'] == lifecycle_state), None)
    if existing:
        existing.update({'fingerprint': fp, 'taken_at': taken_at,
                         'payload_ref': snap_name,
                         'refresh_count': existing.get('refresh_count', 1) + 1})
    else:
        idx['snapshots'].append({
            'lifecycle_state': lifecycle_state,
            'fingerprint': fp,
            'first_taken_at': taken_at,
            'taken_at': taken_at,
            'payload_ref': snap_name,
            'refresh_count': 1,
        })
    with open(_index_path(sprint_dir), 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    return {'fingerprint': fp, 'payload_ref': snap_name}


def get(sprint_dir, lifecycle_state):
    for s in load_index(sprint_dir)['snapshots']:
        if s['lifecycle_state'] == lifecycle_state:
            return s
    return None
