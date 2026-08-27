# -*- coding: utf-8 -*-
"""一次 checkpoint refresh 的完整流程。

    evidence.json ─┬─▶ lifecycle.resolve()      → lifecycle_state
                   ├─▶ snapshots.record()       → 該 state 的 evidence 快照
                   ├─▶ decisions scaffold       → 可重建的結構（本地）
                   ├─▶ decisions.hydrate()      → 併入 Jira 讀回的人類裁決
                   └─▶ sprints/<s>/lifecycle.json  ← Board renderer 的唯一輸入

用法：
    python3 evidence/lifecycle_run.py [--now 2026-08-28T09:00] [--evidence <path>]

Jira 的讀寫不在這裡（Python 端沒有 MCP）。人類裁決由執行端抓下來放在
sprints/<sprint>/decision_comments.json（一個字串陣列，依時間排序），
本模組只負責解析與合併。檔案不存在就視為「尚未有任何裁決」。
"""
import argparse, copy, json, os, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from config import CONFIG                                    # noqa: E402
import workday as W                                          # noqa: E402
import lifecycle as L                                        # noqa: E402
import snapshots as S                                        # noqa: E402
import decisions as D                                        # noqa: E402
from authored_decisions import AUTHORED, BEFORE_NEXT_SPRINT  # noqa: E402
from paths import sprint_dir as _sprint_dir, evidence_path as _evidence_path  # noqa: E402

ROOT = os.path.join(HERE, '..')


def _now(cfg, override=None):
    tz = timezone(timedelta(hours=8)) if cfg['timezone'] == 'Asia/Taipei' else timezone.utc
    if override:
        return datetime.fromisoformat(override).replace(tzinfo=tz)
    return datetime.now(tz)


def build_scaffold(sprint, evidence):
    """把 authored 的決策定義轉成帶 deterministic id 的結構。

    **不寫入任何 derived state。** issue_scope 只是 key 清單。
    """
    sid = sprint['id']
    out = []
    for seq, a in enumerate(AUTHORED.get(sid, []), start=1):
        out.append({
            'decision_id': D.make_decision_id(sprint['name'], seq),
            'sprint_id': sid,
            'title': a['title'],
            'goal_refs': a['goal_refs'],
            'issue_scope': a['issue_scope'],
            'owner': a['owner'],
            'po_decision_required': a['po_decision_required'],
            'why_now': a['why_now'],
            'ask': a.get('ask'),
            'options': a['options'],
            'if_no_action': a['if_no_action'],
        })
    return out


def render_scope(evidence, issue_scope):
    """用當下的 evidence 把一個 decision 的範圍算出來。

    這是**每次 refresh 都重算**的部分——它不被 persist，也不該被 persist。
    """
    A = evidence['layerA']['issues']
    B = evidence['layerB']['derived']
    R = evidence['layerB']['rollups']

    members = []
    for k in issue_scope:
        members.append(k)
        members += R.get(k, {}).get('child_keys', [])
    members = [k for k in dict.fromkeys(members) if k in A]

    by_role = {}
    for k in members:
        by_role.setdefault(A[k]['status_role'] or 'UNMAPPED', []).append(k)

    sigs = {}
    for k in members:
        for s in B[k]['signals']:
            sigs.setdefault(s['type'], []).append(k)

    return {
        'member_count': len(members),
        'by_role': {r: sorted(v) for r, v in sorted(by_role.items())},
        'closed': len(by_role.get('CLOSED', [])),
        'unassigned': sorted(k for k in members if not A[k]['assignee']),
        'signal_index': {t: sorted(v) for t, v in sorted(sigs.items())},
        'open_items': [
            {'key': k, 'status': A[k]['status_name'], 'assignee': A[k]['assignee'],
             'priority': A[k]['priority'],
             'signals': [s['type'] for s in B[k]['signals']]}
            for k in sorted(members) if A[k]['status_role'] != 'CLOSED'
        ],
    }


def run(evidence_path, now_iso=None, cfg=None, write=True):
    cfg = cfg or copy.deepcopy(CONFIG)
    with open(evidence_path, encoding='utf-8') as f:
        ev = json.load(f)

    sp = ev['layerA']['sprint']
    wd = W.from_config(cfg)
    now = _now(cfg, now_iso)
    lc = L.resolve(sp, now, cfg, wd)

    sprint_dir = _sprint_dir(sp['name'])
    state = lc['lifecycle_state']

    snap = None
    if write:
        snap = S.record(sprint_dir, evidence_path, state, now.isoformat())

    # decision 結構只在進入 CLOSING_DECISION 之後才存在
    scaffold = []
    if state in (L.CLOSING_DECISION, L.FINAL_DAY_EXECUTION, L.SPRINT_CLOSURE):
        existing = D.load_scaffold(sprint_dir)
        scaffold = existing or build_scaffold(sp, ev)
        if state == L.CLOSING_DECISION and not existing:
            # 第一次進入 T-2 才寫入 created_fingerprint，之後不再改
            fp = (snap or {}).get('fingerprint') or S.fingerprint(evidence_path)
            for r in scaffold:
                r['created_fingerprint'] = fp
                r['created_at'] = now.isoformat()
        if write and scaffold:
            D.save_scaffold(sprint_dir, scaffold)

    # 人類裁決：從執行端抓下來的 Jira 留言解析
    comments_path = os.path.join(sprint_dir, 'decision_comments.json')
    bodies = []
    if os.path.exists(comments_path):
        with open(comments_path, encoding='utf-8') as f:
            bodies = json.load(f)
    human = D.parse_comments(bodies)
    hydrated = D.hydrate(scaffold, human)

    # 每個 decision 的當下範圍（每次 refresh 重算，不 persist）
    for r in hydrated:
        r['scope_state'] = render_scope(ev, r['issue_scope'])

    out = {
        'schema': 'sprint-lifecycle/1.0',
        'sprint': {'id': sp['id'], 'name': sp['name'], 'state': sp['state']},
        'lifecycle': lc,
        'evidence': {'path': os.path.relpath(evidence_path, ROOT),
                     'fingerprint': (snap or {}).get('fingerprint')
                                    or S.fingerprint(evidence_path)},
        'snapshot_index': S.load_index(sprint_dir)['snapshots'],
        'closing_decisions': hydrated,
        'before_next_sprint': BEFORE_NEXT_SPRINT.get(sp['id'], []),
        'human_decision_source': {
            'issue': cfg['decision_log_issue'],
            'marker': D.MARKER,
            'comments_seen': len(bodies),
            'decisions_with_human_input': sum(
                1 for r in hydrated if r['human_source'] == 'JIRA_DECISION_LOG'),
        },
    }
    if write:
        os.makedirs(sprint_dir, exist_ok=True)
        with open(os.path.join(sprint_dir, 'lifecycle.json'), 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--now')
    ap.add_argument('--evidence', default=_evidence_path())
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()
    r = run(args.evidence, args.now, write=not args.dry)
    lc = r['lifecycle']
    print('sprint          :', r['sprint']['name'], '(', r['sprint']['state'], ')')
    print('now             :', lc['now_local'])
    print('lifecycle_state :', lc['lifecycle_state'], '—', lc['reason'])
    print('T-1 / T-2       :', lc['anchors']['last_working_day'], '/',
          lc['anchors']['second_last_working_day'])
    print('remaining wd    :', lc['remaining_working_days'])
    print('evidence fp     :', r['evidence']['fingerprint'])
    print('decisions       :', len(r['closing_decisions']),
          '| 已有人類裁決:', r['human_decision_source']['decisions_with_human_input'])
    for d in r['closing_decisions']:
        sc = d['scope_state']
        print('   %s %-24s %-16s scope %d 張 · 已完成 %d · 未指派 %d'
              % (d['decision_id'], d['title'][:22], d['decision_taken'],
                 sc['member_count'], sc['closed'], len(sc['unassigned'])))
