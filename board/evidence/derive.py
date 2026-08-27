# -*- coding: utf-8 -*-
"""LAYER B · Shared Deterministic Derivation.

判準：Board / Thursday / Friday 對同一輸入**理論上只能有一個正確答案**的東西，才放這裡。
這一層不知道「現在是週幾」、不知道「誰在做什麼管理決策」，也不產生任何建議。

本檔案不新增任何 signal——所有規則都是從既有 Board 產生器（gen2.py / data2.py）
搬過來的，語意逐條對齊，見 evidence/PROVENANCE.md。
"""
from datetime import date, timedelta

ROLE_ORDER = {'BACKLOG': 0, 'ACTIVE': 1, 'DELIVERY_COMPLETE': 2, 'CLOSED': 3}
SPLIT_DAYS = 3          # 與 gen2.py 的 SPLIT_DAYS 相同


# ── 小工具 ────────────────────────────────────────────────────────────
def d(s):
    if not s:
        return None
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def ts_date(s):
    """'2026-08-19T16:26:30.246+0800' → date(2026,8,19)（保留 Jira 回傳的當地時區）"""
    if not s:
        return None
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def wd(a, b):
    """a → b 的工作天數，可為負。與 gen2.py 的 wd() 相同。"""
    if not a or not b:
        return None
    step = 1 if b >= a else -1
    n, c = 0, a
    while c != b:
        c += timedelta(days=step)
        if c.weekday() < 5:
            n += step
    return n


# ── 執行事實（從 changelog 推導，只有一個正確答案）────────────────────
def execution_facts(iss):
    """actual_start / actual_end / first_delivery_complete / reopen"""
    trs = sorted(iss['transitions'], key=lambda t: t['at'])
    actual_start = None
    first_dc = None
    first_closed = None
    for t in trs:
        r = t.get('to_role')
        if r == 'ACTIVE' and actual_start is None:
            actual_start = t['at']
        if r == 'DELIVERY_COMPLETE' and first_dc is None:
            first_dc = t['at']
        if r == 'CLOSED' and first_closed is None:
            first_closed = t['at']

    # reopen 只計 actual_start 之後的回退（Contract v1.1 裁決）
    reopens = []
    if actual_start:
        for t in trs:
            if t['at'] <= actual_start:
                continue
            fo, to = ROLE_ORDER.get(t.get('from_role')), ROLE_ORDER.get(t.get('to_role'))
            if fo is not None and to is not None and to < fo and fo >= 2:
                reopens.append(t['at'])

    # 從交付態退回執行態的原始紀錄。與 is_reopened **不同**：
    # Contract 規定 reopen 只計 actual_start 之後的回退，但 877 這種
    # 「To Do → DEV DONE →（退回）In Progress」的卡，退回發生在 actual_start 之前，
    # 因此 is_reopened=False，而退回事件本身確實存在。想描述「複測退回」的 View
    # 必須讀這一欄，不能讀 is_reopened。見 mismatch M-17。
    regressed = [t['at'] for t in trs
                 if ROLE_ORDER.get(t.get('from_role'), -1) >= 2
                 and ROLE_ORDER.get(t.get('to_role'), 99) < ROLE_ORDER.get(t.get('from_role'), -1)]

    # 有 actual_end 但沒有合法開工紀錄 → MISSING_ACTUAL_START_HISTORY
    reached_end = first_closed or first_dc
    missing_start_history = bool(reached_end and not actual_start)

    return {
        'actual_start': actual_start,
        'first_delivery_complete': first_dc,
        'first_closed': first_closed,
        # Board 現行語意：actual_end ＝ 首次進 CLOSED（DEV DONE 不算完成）
        # 與 Contract 文字（首次達 DELIVERY_COMPLETE 或更後階）不一致 → 見 mismatch M-9
        'actual_end': first_closed,
        'never_active': actual_start is None,
        'reopen_count': len(reopens),
        'is_reopened': bool(reopens),
        'regressed_from_delivery_at': regressed,
        'regressed_from_delivery': bool(regressed),
        'missing_actual_start_history': missing_start_history,
    }


# ── 計畫基準的可比對性 ────────────────────────────────────────────────
def baseline(iss, sprint_start, facts):
    """回傳 (classification, baseline_set_at, reason)

    PLANNED      計畫日期的**首次寫入時間**早於 Sprint 開始，且早於該卡任何執行事件
    BACKDATED    寫入時間晚於上述任一者 → 不得用來計算偏差量
    NO_PLAN      沒有計畫日期
    UNVERIFIABLE 有計畫日期，但 changelog 沒有任何寫入紀錄（＝建卡當下就填了，
                 而 issue.created 不在本次抓取範圍）→ 無法驗證，比照不可比對處理
    """
    if not iss['planned_start'] and not iss['planned_end']:
        return 'NO_PLAN', None, '沒有 Start date 也沒有 duedate'

    writes = sorted(iss['date_writes'], key=lambda w: w['at'])
    if not writes:
        return 'UNVERIFIABLE', None, 'changelog 沒有日期寫入紀錄，無法判斷寫入時間'

    set_at = writes[0]['at']
    set_d = ts_date(set_at)

    events = [ts_date(x) for x in (facts['actual_start'],
                                   facts['first_delivery_complete'],
                                   facts['first_closed']) if x]
    first_event = min(events) if events else None

    if first_event and set_d >= first_event:
        return 'BACKDATED', set_at, '計畫日期寫入時間不早於該卡首次執行事件'
    if set_d >= sprint_start:
        return 'BACKDATED', set_at, '計畫日期寫入時間不早於 Sprint 開始'
    return 'PLANNED', set_at, '計畫日期寫入時間早於 Sprint 開始且早於任何執行事件'


# ── 執行訊號（deterministic，不含任何管理判斷）────────────────────────
def signals(iss, facts, base_class, today, sprint_end):
    """回傳 list[dict]。每個 signal 只有 type / level / 可計算的量值。

    這裡的 type 與 gen2.py 的 dev_of() 一對一對應，沒有新增。
    level: 'red' | 'amber' | 'info'（對應 Board 的 tag bad / tag warn / tag）
    """
    out = []
    ps, pe = d(iss['planned_start']), d(iss['planned_end'])
    closed = iss['status_role'] == 'CLOSED'
    comparable = (base_class == 'PLANNED')

    # 1) 工期過長 → 建議拆卡（看計畫值本身，與寫入時間無關）
    if ps and pe and not closed:
        dur = wd(ps, pe) + 1
        if dur > SPLIT_DAYS:
            out.append({'type': 'OVERSIZED_PLANNED_DURATION', 'level': 'amber',
                        'planned_working_days': dur, 'threshold': SPLIT_DAYS})

    # 2) 截止日狀態（事實陳述，不論日期何時寫入）
    if pe and not closed:
        v = wd(today, pe)
        if v < 0:
            if comparable:
                out.append({'type': 'OVERDUE', 'level': 'red', 'working_days': -v})
            elif iss['status_role'] != 'DELIVERY_COMPLETE':
                out.append({'type': 'DUE_DATE_PASSED', 'level': 'red',
                            'planned_end': iss['planned_end']})
        elif v == 0:
            out.append({'type': 'DUE_TODAY', 'level': 'red'})
        elif v == 1:
            out.append({'type': 'DUE_TOMORROW', 'level': 'red'})
        elif v == 2:
            out.append({'type': 'DUE_IN_2_WORKING_DAYS', 'level': 'amber'})

    # 3) 開工偏差（只有計畫日期可比對時才算得出來）
    if comparable:
        a0 = ts_date(facts['actual_start'])
        if a0 and ps and a0 > ps:
            out.append({'type': 'STARTED_LATE', 'level': 'red', 'working_days': wd(ps, a0)})
        if not a0 and ps and ps < today and iss['status_role'] == 'BACKLOG':
            out.append({'type': 'START_DELAY', 'level': 'red',
                        'planned_start': iss['planned_start']})
        if pe and pe > sprint_end:
            out.append({'type': 'PLAN_EXTENDS_BEYOND_SPRINT', 'level': 'info',
                        'planned_end': iss['planned_end']})

    # 4) 卡在 DEV DONE
    if iss['status_role'] == 'DELIVERY_COMPLETE' and facts['first_delivery_complete']:
        dd = wd(ts_date(facts['first_delivery_complete']), today)
        if dd and dd >= 2:
            out.append({'type': 'STUCK_IN_DELIVERY_COMPLETE', 'level': 'red',
                        'working_days': dd})
    return out


# ── 母子卡 roll-up ────────────────────────────────────────────────────
def rollups(issues):
    kids = {}
    for k, v in issues.items():
        if v['parent']:
            kids.setdefault(v['parent'], []).append(k)
    out = {}
    for pk, ks in kids.items():
        rows = [issues[k] for k in ks if k in issues]
        out[pk] = {
            'child_keys': sorted(ks),
            'total': len(rows),
            'closed': sum(1 for r in rows if r['status_role'] == 'CLOSED'),
            'delivery_complete': sum(1 for r in rows if r['status_role'] == 'DELIVERY_COMPLETE'),
            'unassigned': sum(1 for r in rows if not r['assignee']),
            'unassigned_keys': sorted(r['key'] for r in rows if not r['assignee']),
            'by_assignee': _count([r['assignee'] or '未指派' for r in rows]),
        }
    return out


def dependency_edges(issues):
    """issuelinks 正規化成無向去重的邊，並區分「兩端都在本期」與「指向期外」。

    Board / Thursday / Friday 都曾寫過「期內 0 條相依邊」——那是直接數 raw links
    得到的結果，並不精確。這裡把定義收成一份：
      blocking = 連結型別含 Blocks；其餘（Relates 等）不是阻擋關係
    """
    seen, edges = set(), []
    for k, v in issues.items():
        for l in v['issuelinks']:
            other = l.get('inward_key') or l.get('outward_key')
            if not other:
                continue
            pair = tuple(sorted([k, other]))
            typ = l.get('type') or ''
            if (pair, typ) in seen:
                continue
            seen.add((pair, typ))
            edges.append({
                'a': pair[0], 'b': pair[1], 'type': typ,
                'blocking': 'block' in typ.lower(),
                'both_in_sprint': (pair[0] in issues and pair[1] in issues),
            })
    return {
        'edges': edges,
        'total': len(edges),
        'in_sprint': sum(1 for e in edges if e['both_in_sprint']),
        'in_sprint_blocking': sum(1 for e in edges
                                  if e['both_in_sprint'] and e['blocking']),
        'crossing_out_of_sprint': sum(1 for e in edges if not e['both_in_sprint']),
    }


def _count(xs):
    c = {}
    for x in xs:
        c[x] = c.get(x, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


# ── 對外主函式 ────────────────────────────────────────────────────────
def build_layer_b(layer_a, today):
    sp = layer_a['sprint']
    sprint_start = d(sp['startDate'][:10])
    sprint_end = d(sp['endDate'][:10])
    issues = layer_a['issues']

    derived = {}
    for k, iss in issues.items():
        facts = execution_facts(iss)
        bclass, bset, breason = baseline(iss, sprint_start, facts)
        derived[k] = {
            **facts,
            'baseline_class': bclass,
            'baseline_set_at': bset,
            'baseline_reason': breason,
            'has_planned_dates': bool(iss['planned_start'] or iss['planned_end']),
            'signals': signals(iss, facts, bclass, today, sprint_end),
        }
    return {
        'sprint_window': {'start': sprint_start.isoformat(),
                          'end': sprint_end.isoformat(),
                          'end_time_local': sp['endDate']},
        'as_of': today.isoformat(),
        'derived': derived,
        'rollups': rollups(issues),
        'dependencies': dependency_edges(issues),
    }
