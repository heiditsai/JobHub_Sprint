# -*- coding: utf-8 -*-
"""組裝 canonical Sprint Evidence Snapshot。

    Raw Jira Fetch → Shared Evidence / Derivation → Sprint Evidence Snapshot

Snapshot 是三個 View 的**唯一** shared 輸入。View 不得回頭讀 raw，
也不得自行重算 layerB 裡已經有的任何東西。
"""
import json, os, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from normalize import build_layer_a, RAW, STATUS_ROLE            # noqa: E402
from derive import build_layer_b                                  # noqa: E402
from human import build_layer_d                                   # noqa: E402

SCHEMA_VERSION = 'sprint-evidence/1.0'


def detect_mismatches(a, b, dlayer):
    """實作過程中發現的 Contract ↔ Reality 落差。只登記，不自行補規則。"""
    m = []
    issues, derived = a['issues'], b['derived']

    unver = [k for k, v in derived.items() if v['baseline_class'] == 'UNVERIFIABLE']
    if unver:
        m.append({
            'id': 'M-9', 'severity': 'blocking-for-baseline',
            'title': '有計畫日期但 changelog 無寫入紀錄，無法驗證 baseline 來源',
            'detail': '這些卡的日期是在建卡當下填的，Jira 不會為建卡值產生 changelog。'
                      '要判斷寫入時間需要 issue.created，而本次抓取的 fields 不含它。'
                      '目前一律視為不可比對（＝不畫計畫線、不計偏差量），與 Board 現行行為一致。',
            'keys': sorted(unver), 'count': len(unver),
            'resolution': 'NOT RESOLVED — 需 PO 裁決是否把 created 納入 Layer A',
        })

    m.append({
        'id': 'M-10', 'severity': 'semantic',
        'title': 'actual_end 的定義：Contract 文字與 Board 實作不一致',
        'detail': 'Contract 記載 actual_end ＝ 首次達到 DELIVERY_COMPLETE 或更後階；'
                  'Board 實作為首次進入 CLOSED（DEV DONE 不視為完成）。'
                  '本 snapshot 同時輸出 first_delivery_complete 與 first_closed，'
                  'actual_end 沿用 Board 語意以維持 regression。',
        'resolution': 'NOT RESOLVED — 兩者並存，等 PO 裁決哪個是 canonical',
    })

    miss = [k for k, v in derived.items() if v['missing_actual_start_history']]
    if miss:
        m.append({
            'id': 'M-11', 'severity': 'informational',
            'title': '有完工事件但無合法開工紀錄（MISSING_ACTUAL_START_HISTORY）',
            'detail': '不得推定 actual_start ＝ actual_end。依賴 actual_start 的判定為 '
                      'NOT_EVALUABLE；FINISHED_LATE／OVERDUE 仍照常評估。',
            'keys': sorted(miss), 'count': len(miss),
            'resolution': 'BY DESIGN — Contract 已定義此行為',
        })

    if not dlayer['goal_work_map_evaluable']:
        m.append({
            'id': 'M-12', 'severity': 'blocking-for-goal-layer',
            'title': 'Goal → 卡號歸屬沒有任何合法來源',
            'detail': '所有 Goal 層級判斷為 NOT_EVALUABLE。不得以語意推論補上。',
            'resolution': 'NOT RESOLVED — 即 05 區的 1c',
        })
    elif dlayer['goal_work_map_source'] == 'PO_DECLARED_NOT_IN_JIRA':
        m.append({
            'id': 'M-12', 'severity': 'blocking-for-automation',
            'title': 'Goal → 卡號歸屬存在，但不在 Jira 裡',
            'detail': 'Sprint 14 的歸屬是 PO 口頭宣告後由本專案記錄的，'
                      'Jira 沒有承載它的欄位或物件。因此這一項無法在無人值守的排程中重建。',
            'resolution': 'NOT RESOLVED — 即 05 區的 1c',
        })

    for w in dlayer['parse_warnings']:
        m.append({
            'id': 'M-13', 'severity': 'informational',
            'title': 'Personal Goal 的分隔寫法沒有硬邊界',
            'detail': '%s：%s' % (w['who'], w['detail']),
            'resolution': 'NOT RESOLVED — 即 05 區的 1b',
        })

    noflag = all(not i['issuelinks'] for i in issues.values())
    if noflag:
        m.append({
            'id': 'M-14', 'severity': 'informational',
            'title': '期內沒有任何 issuelinks 相依邊',
            'detail': '看板因此無法呈現「A 擋住 B」。這是**沒有邊可畫**，'
                      '不得反推「所以沒有相依」。',
            'resolution': 'BY DESIGN — 資料缺漏，不是執行風險',
        })

    incomplete = [k for k, v in issues.items() if v['changelog_complete'] is False]
    if incomplete:
        m.append({
            'id': 'M-15', 'severity': 'blocking',
            'title': 'changelog 被截斷，衍生值可能不完整',
            'keys': sorted(incomplete), 'count': len(incomplete),
            'resolution': 'NOT RESOLVED',
        })
    return m


def build(sprint_id=8765, today=None, suffix=''):
    today = today or date.today()
    a = build_layer_a(
        os.path.join(RAW, 'issues_parent%s.json' % suffix),
        os.path.join(RAW, 'issues_sub%s.json' % suffix),
        os.path.join(RAW, 'changelog', 'all.json'),
        sprint_id)
    b = build_layer_b(a, today)
    dl = build_layer_d(a)
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_for': {'sprint_id': sprint_id,
                          'sprint_name': a['sprint']['name'],
                          'as_of': today.isoformat()},
        'provenance': {
            'layerA': 'Atlassian MCP · searchJiraIssuesUsingJql + getJiraIssue(expand=changelog)',
            'layerB': 'evidence/derive.py — deterministic，無新增 signal',
            'layerD': 'Jira 衝刺目標欄位（Goal 文字）＋ PO 宣告（Goal→卡號歸屬，不在 Jira）',
            'status_role_map': STATUS_ROLE,
        },
        'layerA': a,
        'layerB': b,
        'layerD': dl,
        'mismatches': detect_mismatches(a, b, dl),
    }


if __name__ == '__main__':
    suffix = sys.argv[1] if len(sys.argv) > 1 else ''
    ev = build(8765, date(2026, 8, 27), suffix)
    out = os.path.join(HERE, '..', 'sprints', 'sprint-14')
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, 'evidence%s.json' % ('-frozen' if suffix else ''))
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(ev, f, ensure_ascii=False, indent=1, sort_keys=False)
    print('wrote', os.path.relpath(p), os.path.getsize(p), 'bytes')
    print('issues:', len(ev['layerA']['issues']))
    sig = {}
    for v in ev['layerB']['derived'].values():
        for s in v['signals']:
            sig[s['type']] = sig.get(s['type'], 0) + 1
    print('signals:', dict(sorted(sig.items())))
    bc = {}
    for v in ev['layerB']['derived'].values():
        bc[v['baseline_class']] = bc.get(v['baseline_class'], 0) + 1
    print('baseline:', bc)
    print('mismatches:', [(m['id'], m['severity']) for m in ev['mismatches']])
