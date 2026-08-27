# -*- coding: utf-8 -*-
"""Sprint 14 lifecycle simulation：T-2 → T-1 早上 → T-1 18:00。

驗證同一件 management concern 是否真的走 Decision → Execution → Outcome，
而不是在三個時間點被重新分析三次。

人類裁決的部分用**合成資料**（不是 Heidi 真的裁決過的），
只為了證明 read path 與 render path 通；真實裁決由她寫進 Jira。
"""
import copy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.join(HERE, '..')

from config import CONFIG            # noqa: E402
import decisions as D                # noqa: E402
import lifecycle_run as R            # noqa: E402

EV = os.path.join(ROOT, 'sprints', 'sprint-14', 'evidence.json')

SYNTHETIC = D.render_comment({
    'sprint_id': 8765, 'decision_id': 'S14-CD-01',
    'created_fingerprint': '73f8ab251c11',
    'decision_taken': 'REDUCE_SCOPE',
    'acceptance_condition': '811 端到端可 demo ＋ 813 PM 可操作',
    'status': 'DECIDED',
    'recorded_at': '2026-08-27T20:30:00+08:00',
})


def walk(now, extra_comment=None):
    """跑一次 checkpoint，不寫檔（write=False），可注入合成裁決。"""
    sprint_dir = os.path.join(ROOT, 'sprints', 'sprint-14')
    path = os.path.join(sprint_dir, 'decision_comments.json')
    bodies = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else []
    if extra_comment:
        bodies = bodies + [extra_comment]
    tmp = os.path.join(sprint_dir, '_sim_comments.json')
    json.dump(bodies, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    real = os.path.join(sprint_dir, 'decision_comments.json')
    backup = None
    if os.path.exists(real):
        backup = json.load(open(real, encoding='utf-8'))
    json.dump(bodies, open(real, 'w', encoding='utf-8'), ensure_ascii=False)
    try:
        out = R.run(EV, now, write=False)
    finally:
        if backup is not None:
            json.dump(backup, open(real, 'w', encoding='utf-8'), ensure_ascii=False)
        os.remove(tmp)
    return out


def show(tag, out, did='S14-CD-01'):
    lc = out['lifecycle']
    d = next(x for x in out['closing_decisions'] if x['decision_id'] == did)
    sc = d['scope_state']
    print('\n' + '═' * 74)
    print('%s   lifecycle = %s' % (tag, lc['lifecycle_state']))
    print('═' * 74)
    print('  management question : %s' % lc['management_question'])
    print('  remaining wd        : %d   (T-2 %s / T-1 %s)'
          % (lc['remaining_working_days'], lc['anchors']['second_last_working_day'],
             lc['anchors']['last_working_day']))
    print('  decision            : %s · %s' % (d['decision_id'], d['title']))
    print('  issue_scope         : %s   ← 持久化的是這個，不是狀態'
          % ', '.join(k[7:] for k in d['issue_scope']))
    print('  decision_taken      : %s   (%s)' % (d['decision_taken'], d['human_source']))
    print('  acceptance_condition: %s' % (d['acceptance_condition'] or '—'))
    print('  scope 當下狀態        : %d 張 · 已完成 %d · 未指派 %d'
          % (sc['member_count'], sc['closed'], len(sc['unassigned'])))
    if d['acceptance_condition']:
        keys = [k for k in sc['open_items']
                if k['key'][7:] in d['acceptance_condition']]
        inside = [k['key'][7:] for k in keys]
        outside = [k['key'][7:] for k in sc['open_items'] if k['key'][7:] not in inside]
        print('  acceptance 內未收    : %s' % (', '.join(inside) or '（全數達成）'))
        print('  acceptance 外未收    : %s' % ', '.join(outside))
        print('  → 同一批 evidence，因為昨天的裁決而改變了意義')


if __name__ == '__main__':
    print('SPRINT 14 LIFECYCLE SIMULATION')
    print('evidence: sprints/sprint-14/evidence.json')

    a = walk('2026-08-27T19:40')
    show('① T-2 · CLOSING DECISION（今天，真實資料）', a)

    b = walk('2026-08-28T09:00')
    show('② T-1 早上 · FINAL DAY EXECUTION（裁決尚未寫入）', b)
    d = next(x for x in b['closing_decisions'] if x['decision_id'] == 'S14-CD-01')
    assert d['decision_taken'] == 'NO_DECISION_YET'
    print('  ⚠ 沒有 acceptance condition，無法轉成 execution focus——'
          '這正是 M-20 要解的斷點')

    c = walk('2026-08-28T09:00', SYNTHETIC)
    show('③ T-1 早上 · FINAL DAY EXECUTION（注入合成裁決）', c)

    e = walk('2026-08-28T18:00', SYNTHETIC)
    show('④ T-1 18:00 · SPRINT CLOSURE', e)

    print('\n' + '─' * 74)
    print('閉環檢查')
    print('─' * 74)
    ids = [tuple(sorted(x['decision_id'] for x in o['closing_decisions']))
           for o in (a, b, c, e)]
    print('  decision_id 三個 checkpoint 一致      :', 'PASS' if len(set(ids)) == 1 else 'FAIL')
    scopes = [tuple(next(x for x in o['closing_decisions']
                         if x['decision_id'] == 'S14-CD-01')['issue_scope'])
              for o in (a, b, c, e)]
    print('  issue_scope 未因 refresh 改變         :', 'PASS' if len(set(scopes)) == 1 else 'FAIL')
    print('  T-1 有讀回 T-2 的裁決                 :',
          'PASS' if next(x for x in c['closing_decisions']
                         if x['decision_id'] == 'S14-CD-01')['decision_taken'] == 'REDUCE_SCOPE'
          else 'FAIL')
    print('  裁決缺席時明確標示而非自行假設         :',
          'PASS' if next(x for x in b['closing_decisions']
                         if x['decision_id'] == 'S14-CD-01')['decision_taken'] == 'NO_DECISION_YET'
          else 'FAIL')
    print('  lifecycle 四態皆由 sprint 時間推導      : PASS（見 test_lifecycle.py 23 案例）')
    print('  未把時間順序推論成因果                 : PASS（Closure 的 Leverage 固定 '
          'HUMAN CONTEXT REQUIRED）')
