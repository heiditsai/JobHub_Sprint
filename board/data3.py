# -*- coding: utf-8 -*-
"""Board 的 data layer —— 改由 Shared Evidence Snapshot 供應。

    sprints/sprint-14/evidence.json  →  Board 需要的所有變數

取代 data2.py。差別只有一個，但很重要：
  data2.py 的 changelog（CL{}）是**人工逐張讀 Jira 抄進去的**，只涵蓋 15 張卡。
  這裡的每一個值都來自 evidence layer，涵蓋全部 113 張，而且是程式抓的。

**沒有新增任何 signal，也沒有改任何判定規則。**
baseline_class / actual dates / never_active 全部直接讀 evidence 的 Layer B，
Board 不再自己算一次。
"""
import collections, json, os
from datetime import date, timedelta

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence'))
from paths import evidence_path as _evidence_path          # noqa: E402
EVIDENCE_PATH = _evidence_path()
with open(EVIDENCE_PATH, encoding='utf-8') as _f:
    EV = json.load(_f)

# 原始資料的抓取時刻。頁首原本寫死成 "2026-08-27 16:05"，
# 改成讀 raw 檔的 fetched_at —— 抓不到就是 None，由呈現端說「不明」，不猜。
FETCHED_AT = None
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'evidence', 'raw', 'issues_parent.json'), encoding='utf-8') as _rf:
        FETCHED_AT = json.load(_rf).get('fetched_at')
except Exception:
    pass

_A = EV['layerA']['issues']
_B = EV['layerB']['derived']
_R = EV['layerB']['rollups']
_D = EV['layerD']
_SP = EV['layerA']['sprint']

# ── 狀態字典（與 data2.py 相同）───────────────────────────────────────
SK = {'待辦事項': 'todo', '進行中': 'doing', '測試中': 'testing',
      'DEV DONE': 'devdone', '完成': 'done'}
STL = {'todo': 'To Do', 'doing': 'In Progress', 'testing': 'Testing',
       'devdone': 'Dev Done', 'done': 'Done'}
ICON = {'todo': '○', 'doing': '◐', 'testing': '◑', 'devdone': '◕', 'done': '●'}
# evidence 帶得回語意角色，但 Board 的五階顯示沿用原字典；
# 未映射的狀態（例如 11854「取消」）保留原名，不硬塞進五階 → 見 M-16
ROLE_FALLBACK = {'BACKLOG': 'todo', 'ACTIVE': 'doing',
                 'DELIVERY_COMPLETE': 'devdone', 'CLOSED': 'done'}


def d(s):
    if not s or s == '—':
        return None
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def wd(a, b):
    if not a or not b:
        return None
    step = 1 if b >= a else -1
    n, c = 0, a
    while c != b:
        c += timedelta(days=step)
        if c.weekday() < 5:
            n += step
    return n


# ── Sprint 與日曆 ────────────────────────────────────────────────────
_w = EV['layerB']['sprint_window']
TODAY = d(EV['layerB']['as_of'])
_end_local = _SP['endDate']
SPRINT = dict(name=_SP['name'], start=d(_w['start']), end=d(_w['end']),
              endTime='15:00', goal='\n'.join(_D['team_goals']))

DAYS = []
_c = SPRINT['start']
while _c <= SPRINT['end']:
    if _c.weekday() < 5:
        DAYS.append((_c, _c.strftime('%m/%d'), '一二三四五六日'[_c.weekday()]))
    _c += timedelta(days=1)


# ── 卡片 ─────────────────────────────────────────────────────────────
def _row(v):
    st = SK.get(v['status_name'])
    if st is None:                      # 未映射的狀態：保留原名，不猜
        st = ROLE_FALLBACK.get(v['status_role'], 'todo')
    return dict(key=v['key'], sum=v['summary'], st=st,
                who=v['assignee'] or '未指派',
                pri=v['priority'] or '-',
                pstart=v['planned_start'], pend=v['planned_end'],
                lab=v['labels'], parent=v['parent'],
                type=v['issuetype'],
                status_name=v['status_name'],
                status_role=v['status_role'])


M = [_row(v) for v in _A.values() if v['level'] == 'parent']
S = [_row(v) for v in _A.values() if v['level'] == 'sub']
M.sort(key=lambda x: x['key'])
S.sort(key=lambda x: x['key'])
BY = {m['key']: m for m in M}
SBY = {x['key']: x for x in S}
SUB = {}
for _x in S:
    SUB.setdefault(_x['parent'], []).append(_x)

# 未映射狀態的卡（M-16 未裁決前，據實記錄不隱藏）
UNMAPPED_STATUS = sorted(k for k, v in _A.items() if v['status_role'] is None)


# ── changelog 衍生值：**直接讀 evidence，不再自己算** ──────────────────
def _dt(x):
    return x[:10] if x else '—'


def _note(k):
    """把 evidence 的 baseline 判定轉成一句人看得懂的話。

    data2.py 這裡是手寫的散文；現在改成由 baseline_set_at 與執行事件的
    時間差**算出來**，所以每張卡都有，不再只有手抄過的那 15 張。
    """
    b = _B[k]
    if b['baseline_class'] != 'BACKDATED' or not b['baseline_set_at']:
        return ''
    set_at = b['baseline_set_at']
    hhmm = set_at[11:16]
    day = set_at[:10]
    evs = [(x, lab) for x, lab in
           ((b['actual_start'], '開工'), (b['first_delivery_complete'], '進 DEV DONE'),
            (b['first_closed'], '完成')) if x]
    if not evs:
        return '計畫日 %s %s 寫入，晚於 Sprint 開始' % (day[5:], hhmm)
    first, lab = min(evs, key=lambda e: e[0])
    delta_days = (d(day) - d(first[:10])).days     # 正 = 計畫日晚於事件 = 事後回填
    if delta_days > 0:
        return '計畫日在卡片 %s 之後 %d 天才回填' % (lab, delta_days)
    if delta_days < 0:
        return '計畫日 %s %s 寫入，%s 前 %d 天' % (day[5:], hhmm, lab, -delta_days)
    # 同一天：比到分鐘，再比到小時
    if set_at[11:16] == first[11:16]:
        return '計畫日與 %s 同一分鐘寫入' % lab
    h1 = int(set_at[11:13]) * 60 + int(set_at[14:16])
    h2 = int(first[11:13]) * 60 + int(first[14:16])
    gap = h2 - h1
    if gap > 0:
        return '計畫日 %s %s 寫入，%s 前 %d 小時' % (day[5:], hhmm, lab, max(1, round(gap / 60)))
    return '計畫日 %s %s 寫入，%s 後 %d 小時' % (day[5:], hhmm, lab, max(1, round(-gap / 60)))


CL = {}
for _k, _b in _B.items():
    if not (_b['actual_start'] or _b['first_delivery_complete'] or _b['first_closed']
            or _b['baseline_set_at']):
        continue
    CL[_k] = (_dt(_b['actual_start']), _dt(_b['first_delivery_complete']),
              _dt(_b['actual_end']),
              (_b['baseline_set_at'] or '')[:10] or None,
              _note(_k))

# 從未進過 In Progress（有執行事件但沒有合法開工紀錄）
NO_INPROGRESS = {k for k, v in _B.items()
                 if v['never_active'] and (v['first_delivery_complete'] or v['first_closed'])}

# 從交付態退回執行態的原始紀錄（is_reopened 看不到 actual_start 之前的那種）
REGRESSED_FROM_DELIVERY = sorted(k for k, v in _B.items() if v['regressed_from_delivery'])


def baseline_class(k):
    """直接讀 evidence 的判定。UNVERIFIABLE 比照不可比對處理（與 Board 現行行為一致）。"""
    b = _B.get(k)
    if not b:
        return 'NO_PLAN'
    c = b['baseline_class']
    return 'BACKDATED' if c == 'UNVERIFIABLE' else c


# ── Layer D：Goal ────────────────────────────────────────────────────
SPRINT_GOAL_RAW = _D['goal_field_raw']
ALIAS = _D['alias_map']
TEAM_LINES = _D['team_goals']
PERSONAL_BY_FULLNAME = _D['personal_goal_statements']
UNKNOWN_GOAL_NAMES = _D['unknown_goal_names']
GOAL_PARSE_WARN = ['%s：%s' % (w['who'], w['detail']) for w in _D['parse_warnings']]
GOAL_TEXT_MISSING = _D['goal_statement_missing']
GOAL_UNMAPPED_TEXT = _D['goal_statement_unmapped']
GOAL_TEXT_MISMATCH = []          # evidence 是唯一來源，沒有可比對的第二份

GOALS = []
for _g in _D['goals']:
    GOALS.append(dict(person=_g['person'], role=_g['role'], gid=_g['gid'],
                      theme=_g.get('theme', ''), statement=_g['statement'],
                      work=_g['work'], dep=_g.get('dependency'),
                      reconstructed=_g.get('reconstructed', False),
                      src=_g.get('statement_source')))

TEAM_GOAL_MAP = [(TEAM_LINES[m['team_goal_index']], m['gids'])
                 for m in _D['team_goal_owner_map']]
OUTSIDE_TEAM_GOAL = [g['gid'] for g in _D['goals'] if g.get('non_team_goal_aligned')]
PARTICIPANTS = _D['participants']
NONPART = _D['non_participants']
GOAL_WORK = {k for g in GOALS for k in g['work']}

# ── 仍為人工撰寫的部分（Layer C 註解，evidence 推導不出來）──────────────
KEY_SUBS = {
    'JOBHUB-866': dict(parent='JOBHUB-863',
                       why='Erica 宣告相依「使 Quincy 下週可串接」的實際交付物'
                           '（契約＋mock，FE 解鎖點）'),
    'JOBHUB-728': dict(parent='JOBHUB-582',
                       why='582 母卡已完成，但此後端 API 子卡仍在進行中'),
}
UNASSIGNED_SUBS = [x for x in S if x['who'] == '未指派' and x['st'] != 'done']

DATA_SOURCE = dict(path=EVIDENCE_PATH,
                   fingerprint=EV.get('generated_for', {}),
                   schema=EV.get('schema_version'),
                   issues=len(_A), with_changelog=len(CL))
