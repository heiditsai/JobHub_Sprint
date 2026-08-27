# -*- coding: utf-8 -*-
"""Closing Decision 的兩層 persistence。

刻意分兩個地方存，因為兩者的性質不同：

┌─ 可重建的結構 ─────────────────────────────────────────────────────┐
│  decision_id / title / goal_refs / issue_scope / owner            │
│  由 evidence ＋ 既有 inclusion rules 決定，                          │
│  同一份 evidence 重跑會得到同一組結果 → **存本地**                     │
│  sprints/<sprint>/decisions.json                                  │
└───────────────────────────────────────────────────────────────────┘

┌─ 不可重建的人類裁決 ────────────────────────────────────────────────┐
│  decision_taken / acceptance_condition                            │
│  只有人知道，任何演算法都推導不出來 → **存 Jira**                      │
│  config['decision_log_issue'] 的 append-only 留言                  │
└───────────────────────────────────────────────────────────────────┘

Jira 留言**只放人的裁決與識別**，不放 derived state，也不放 prose snapshot。
理由很簡單：derived state 幾小時就過期，prose 會讓 lifecycle 僵化；
而這兩者都能用 created_fingerprint 找回原始 snapshot 重現。

本模組不呼叫 Jira。它只負責**格式**（序列化／解析／合併）；
實際讀寫由具備 Atlassian MCP 的執行端完成，見 render_comment() / parse_comments()。
"""
import json, os, re

MARKER = 'SPRINT-DECISION-V1'

# 只有這些欄位可以寫進 Jira 留言
HUMAN_FIELDS = ('decision_taken', 'acceptance_condition', 'status')
IDENTITY_FIELDS = ('sprint_id', 'decision_id', 'created_fingerprint')
ALLOWED_IN_COMMENT = IDENTITY_FIELDS + HUMAN_FIELDS + ('recorded_at',)

# decision_taken 的合法值。AI 不得自創。
DECISION_TAKEN = ('HOLD_SCOPE', 'REDUCE_SCOPE', 'CARRY_FORWARD',
                  'NO_DECISION_YET', 'SUPERSEDED')
STATUS = ('OPEN', 'DECIDED', 'SUPERSEDED', 'CLOSED_OUT')


# ── decision_id ──────────────────────────────────────────────────────
def make_decision_id(sprint_name, seq):
    """S14-CD-01。seq 由**確定性排序**決定（見 build_decision_scaffold），
    所以同一份 evidence 重跑會得到同一個 id，Jira 上的裁決才對得回來。"""
    m = re.search(r'(\d+)\s*$', sprint_name or '')
    n = m.group(1) if m else 'X'
    return 'S%s-CD-%02d' % (n, seq)


# ── Jira 留言格式 ─────────────────────────────────────────────────────
def render_comment(rec):
    """產生要貼到 Jira 的留言字串。**只輸出白名單欄位。**"""
    missing = [f for f in IDENTITY_FIELDS if not rec.get(f)]
    if missing:
        raise ValueError('缺少識別欄位：%s' % missing)
    if rec.get('decision_taken') and rec['decision_taken'] not in DECISION_TAKEN:
        raise ValueError('decision_taken 不在合法值內：%r' % rec['decision_taken'])
    if rec.get('status') and rec['status'] not in STATUS:
        raise ValueError('status 不在合法值內：%r' % rec['status'])

    lines = [MARKER]
    for f in ALLOWED_IN_COMMENT:
        v = rec.get(f)
        if v is None or v == '':
            continue
        if '\n' in str(v):
            raise ValueError('%s 不得含換行（append-only 留言以行為單位解析）' % f)
        lines.append('%s: %s' % (f, v))
    return '\n'.join(lines)


def parse_comment(text):
    """把一則 Jira 留言解析回 dict。不是 decision 留言就回 None。"""
    if not text or MARKER not in text:
        return None
    out = {}
    started = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == MARKER:
            started = True
            continue
        if not started or not line:
            continue
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        k, v = k.strip(), v.strip()
        if k in ALLOWED_IN_COMMENT:      # 白名單以外一律忽略
            out[k] = v
    return out or None


def merge_comments(parsed_list):
    """append-only log → 每個 decision_id 的最終狀態。

    規則：後寫的覆蓋先寫的，**逐欄位**覆蓋（沒寫到的欄位保留舊值）。
    呼叫端必須依 Jira 留言的時間順序傳入。
    """
    out = {}
    for rec in parsed_list:
        if not rec or not rec.get('decision_id'):
            continue
        did = rec['decision_id']
        cur = out.setdefault(did, {'decision_id': did})
        for k, v in rec.items():
            if v not in (None, ''):
                cur[k] = v
    return out


def parse_comments(comment_bodies):
    """便利函式：一串留言字串（依時間排序）→ {decision_id: human_decision}"""
    return merge_comments([parse_comment(c) for c in comment_bodies])


# ── 本地：可重建的 decision 結構 ────────────────────────────────────────
def scaffold_path(sprint_dir):
    return os.path.join(sprint_dir, 'decisions.json')


def save_scaffold(sprint_dir, records):
    os.makedirs(sprint_dir, exist_ok=True)
    p = scaffold_path(sprint_dir)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'schema': 'closing-decision/1.0', 'decisions': records},
                  f, ensure_ascii=False, indent=1)
    return p


def load_scaffold(sprint_dir):
    p = scaffold_path(sprint_dir)
    if not os.path.exists(p):
        return []
    with open(p, encoding='utf-8') as f:
        return json.load(f).get('decisions', [])


def hydrate(records, human_by_id):
    """把 Jira 讀回來的人類裁決合併進本地結構。

    合併後每筆多出：
      decision_taken / acceptance_condition / status / human_source
    讀不到就是 NO_DECISION_YET —— **不猜、不預設 PO 同意了什麼。**
    """
    out = []
    for r in records:
        h = human_by_id.get(r['decision_id']) or {}
        merged = dict(r)
        merged['decision_taken'] = h.get('decision_taken') or 'NO_DECISION_YET'
        merged['acceptance_condition'] = h.get('acceptance_condition')
        merged['status'] = h.get('status') or ('DECIDED' if h.get('decision_taken') else 'OPEN')
        merged['human_source'] = 'JIRA_DECISION_LOG' if h else 'NOT_RECORDED'
        out.append(merged)
    return out
