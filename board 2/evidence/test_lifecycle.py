# -*- coding: utf-8 -*-
"""Lifecycle Test Matrix。純函式測試，不碰 Jira、不碰 evidence。"""
import copy, sys, os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from config import CONFIG                    # noqa: E402
import workday as W                          # noqa: E402
import lifecycle as L                        # noqa: E402

TPE = timezone(timedelta(hours=8))


def cfg(**over):
    c = copy.deepcopy(CONFIG)
    c.update(over)
    return c


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=TPE)


S14 = {'id': 8765, 'name': 'JOBHUB 衝刺 14', 'state': 'active',
       'startDate': '2026-08-24T01:40:36.000Z', 'endDate': '2026-08-28T07:00:00.000Z'}
S13 = {'id': 8762, 'name': 'JOBHUB 衝刺 13', 'state': 'closed',
       'startDate': '2026-08-17T06:58:31.000Z', 'endDate': '2026-08-20T21:20:42.000Z'}
S_MIDNIGHT = {'id': 1, 'name': '收期 00:00', 'state': 'active',
              'startDate': '2026-08-24T01:00:00.000Z', 'endDate': '2026-08-28T00:00:00.000Z'}
S_TWOWEEK = {'id': 2, 'name': '兩週', 'state': 'active',
             'startDate': '2026-08-17T01:00:00.000Z', 'endDate': '2026-08-28T07:00:00.000Z'}
S_ONEDAY = {'id': 3, 'name': '單日', 'state': 'active',
            'startDate': '2026-08-28T01:00:00.000Z', 'endDate': '2026-08-28T07:00:00.000Z'}
S_WED_END = {'id': 4, 'name': '週三收期', 'state': 'active',
             'startDate': '2026-08-24T01:00:00.000Z', 'endDate': '2026-08-26T07:00:00.000Z'}

# 08/28（五）設為假日 → T-1 應退到 08/27（四），T-2 退到 08/26（三）
CFG_HOLIDAY = cfg(holidays=['2026-08-28'])
# 08/29（六）補班 → 不影響 T-1，因為收期在 08/28
CFG_EXTRA = cfg(extra_working_days=['2026-08-29'])
# 收盤 checkpoint 改 16:00
CFG_EARLY_CLOSE = cfg(closure_checkpoint_time='16:00')
# 上班時間改 07:00 → 收期 08:00 的 sprint 不再往前推
CFG_EARLY_START = cfg(workday_start_time='07:00')

CASES = [
    # (名稱, sprint, now, cfg, 期望 state, 期望 T-1, 期望 T-2)
    ('S14 · 週一（正常執行）',        S14, at('2026-08-24T10:00'), CONFIG, L.NORMAL_EXECUTION,    '2026-08-28', '2026-08-27'),
    ('S14 · 週三（正常執行）',        S14, at('2026-08-26T10:00'), CONFIG, L.NORMAL_EXECUTION,    '2026-08-28', '2026-08-27'),
    ('S14 · 週四早上（T-2 收斂決策）', S14, at('2026-08-27T10:00'), CONFIG, L.CLOSING_DECISION,    '2026-08-28', '2026-08-27'),
    ('S14 · 週四深夜（仍是 T-2）',    S14, at('2026-08-27T23:00'), CONFIG, L.CLOSING_DECISION,    '2026-08-28', '2026-08-27'),
    ('S14 · 週五早上（T-1 最後一天）', S14, at('2026-08-28T09:00'), CONFIG, L.FINAL_DAY_EXECUTION, '2026-08-28', '2026-08-27'),
    ('S14 · 週五 15:00 收期後仍未到 checkpoint', S14, at('2026-08-28T15:30'), CONFIG, L.FINAL_DAY_EXECUTION, '2026-08-28', '2026-08-27'),
    ('S14 · 週五 18:00（Closure）',   S14, at('2026-08-28T18:00'), CONFIG, L.SPRINT_CLOSURE,      '2026-08-28', '2026-08-27'),
    ('S14 · 週六（已過 checkpoint）', S14, at('2026-08-29T10:00'), CONFIG, L.SPRINT_CLOSURE,      '2026-08-28', '2026-08-27'),
    ('S14 · state=closed 提早關閉',   dict(S14, state='closed'), at('2026-08-26T10:00'), CONFIG, L.SPRINT_CLOSURE, '2026-08-28', '2026-08-27'),

    ('S13 · 已關閉',                  S13, at('2026-08-20T10:00'), CONFIG, L.SPRINT_CLOSURE,      '2026-08-20', '2026-08-19'),

    ('收期 00:00 → T-1 退一天',       S_MIDNIGHT, at('2026-08-26T10:00'), CONFIG, L.CLOSING_DECISION, '2026-08-27', '2026-08-26'),
    ('收期 00:00 · 週四即最後一天',    S_MIDNIGHT, at('2026-08-27T10:00'), CONFIG, L.FINAL_DAY_EXECUTION, '2026-08-27', '2026-08-26'),
    ('上班時間改 07:00 → 不再退一天',  S_MIDNIGHT, at('2026-08-27T10:00'), CFG_EARLY_START, L.CLOSING_DECISION, '2026-08-28', '2026-08-27'),

    ('兩週 Sprint · 第二個週一仍正常', S_TWOWEEK, at('2026-08-24T10:00'), CONFIG, L.NORMAL_EXECUTION, '2026-08-28', '2026-08-27'),
    ('兩週 Sprint · T-2',            S_TWOWEEK, at('2026-08-27T10:00'), CONFIG, L.CLOSING_DECISION, '2026-08-28', '2026-08-27'),

    ('週三收期 · T-2 是週二',         S_WED_END, at('2026-08-25T10:00'), CONFIG, L.CLOSING_DECISION, '2026-08-26', '2026-08-25'),
    ('週三收期 · T-1 是週三',         S_WED_END, at('2026-08-26T09:00'), CONFIG, L.FINAL_DAY_EXECUTION, '2026-08-26', '2026-08-25'),

    ('假日 08/28 → T-1 退到週四',     S14, at('2026-08-26T10:00'), CFG_HOLIDAY, L.CLOSING_DECISION, '2026-08-27', '2026-08-26'),
    ('假日 08/28 → 週四即 T-1',       S14, at('2026-08-27T10:00'), CFG_HOLIDAY, L.FINAL_DAY_EXECUTION, '2026-08-27', '2026-08-26'),
    ('補班 08/29 不影響 T-1',         S14, at('2026-08-27T10:00'), CFG_EXTRA, L.CLOSING_DECISION, '2026-08-28', '2026-08-27'),

    ('Closure checkpoint 改 16:00',   S14, at('2026-08-28T16:30'), CFG_EARLY_CLOSE, L.SPRINT_CLOSURE, '2026-08-28', '2026-08-27'),
    ('Closure 16:00 · 15:30 仍是最後一天', S14, at('2026-08-28T15:30'), CFG_EARLY_CLOSE, L.FINAL_DAY_EXECUTION, '2026-08-28', '2026-08-27'),

    ('單日 Sprint · 跳過 T-2',        S_ONEDAY, at('2026-08-28T09:00'), CONFIG, L.FINAL_DAY_EXECUTION, '2026-08-28', '2026-08-27'),
]


def run():
    ok = bad = 0
    print('=' * 92)
    print('LIFECYCLE TEST MATRIX')
    print('=' * 92)
    print('%-38s %-22s %-12s %-12s %s' % ('CASE', 'STATE', 'T-1', 'T-2', ''))
    print('-' * 92)
    for name, sprint, now, c, want_state, want_t1, want_t2 in CASES:
        wd = W.from_config(c)
        r = L.resolve(sprint, now, c, wd)
        got = (r['lifecycle_state'], r['anchors']['last_working_day'],
               r['anchors']['second_last_working_day'])
        want = (want_state, want_t1, want_t2)
        mark = '✓' if got == want else '✗'
        if got == want:
            ok += 1
        else:
            bad += 1
        print('%-38s %-22s %-12s %-12s %s' % (name, got[0], got[1], got[2], mark))
        if got != want:
            print('    期望 %s' % (want,))
    print('-' * 92)
    print('通過 %d / %d，失敗 %d' % (ok, ok + bad, bad))

    # 單日 Sprint 的特別檢查
    wd = W.from_config(CONFIG)
    r = L.resolve(S_ONEDAY, at('2026-08-28T09:00'), CONFIG, wd)
    assert r['single_day_sprint'] and r['closing_decision_window_skipped'], \
        '單日 Sprint 應標記為跳過 closing decision 視窗'
    print('單日 Sprint 正確標記 closing_decision_window_skipped ✓')

    # 假日 provider 可替換性檢查
    class AlwaysWorking(W.WorkdayProvider):
        def is_working_day(self, d): return True
        def previous_working_day(self, d, inclusive=False):
            from datetime import timedelta as td
            return d if inclusive else d - td(days=1)
        def working_days_between(self, a, b): return (b - a).days + 1
    r = L.resolve(S14, at('2026-08-27T10:00'), CONFIG, AlwaysWorking())
    assert r['anchors']['second_last_working_day'] == '2026-08-27', \
        '換 provider 後 T-2 應變成 08/27（因為週末也算工作日，T-1 仍是 08/28）'
    print('WorkdayProvider 可替換性 ✓（換成「每天都是工作日」後 T-2 仍正確重算）')
    return bad == 0


if __name__ == '__main__':
    sys.exit(0 if run() else 1)
