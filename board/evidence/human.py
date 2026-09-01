# -*- coding: utf-8 -*-
"""LAYER D · Human Input.

只放**人明確宣告過**的東西，並且每一項都必須帶 source。
AI 不得在這一層做任何語意推論。
"""

import json as _json
import os as _os
import re as _re

ALIAS = {"Quincy": "Quincy Chen", "Bill": "Bill Wang",
         "Erica": "Erica lh Lee", "Lodifa": "Lodifa Chen"}

# 行首的序號／項目符號：`1.` `2、` `3)` `-` `•` `*`，可重複
_LEAD = _re.compile(r'^\s*(?:\d+\s*[.、)]\s*|[-•*+]\s+|[-•*+](?=\S))+')
# 該行是不是條列子項（`- xxx`）
_BULLET = _re.compile(r'^\s*[-•*+]\s*\S')


def _is_person(head):
    """head 是不是名單內的人。**只認 ALIAS 的 key 或 value**。

    這是唯一的護欄：Sprint 15 的 `- 職缺管理 : …` 也長得像 `姓名:一句話`，
    只有靠名單才擋得掉——不能再用「開頭不是數字、長度 <= 12」這種形狀規則。
    """
    if not head:
        return None
    if head in ALIAS:
        return head
    for k, v in ALIAS.items():
        if head == v:
            return k
    return None


def parse_sprint_goal(raw):
    """Jira 衝刺目標欄位 → (team_lines, [(alias, [statement,...])], warnings)

    支援兩種寫法，兩者可混用：

      A（Sprint 14）  `姓名:一句話`，同姓名多行 ＝ 多個 Goal。
         相容：同一行用 `。/` 分隔——只認句號＋斜線，因為單純的 `/`
         會和內文（例如「Bug / 優化」）撞在一起。

      B（Sprint 15）  `1. 姓名：` 自成一行，底下接 `- 一句話` 條列，
         每個條列 ＝ 一個 Goal，直到下一個人名行或非條列行為止。

    硬規則：**人名一定要在 ALIAS 名單內**。認不出人就不是 Goal 行，
    寧可整份 personal goal 是空的並發 warning，也不要把
    `- 職缺管理 : …` 這種條列行收成「人」。
    """
    team, order, byname, warn = [], [], {}, []
    cur = None                      # 目前正在收條列的人（B 寫法）

    def add(who, parts):
        if who not in byname:
            byname[who] = []
            order.append(who)
        byname[who] += parts

    for ln in (raw or '').split('\n'):
        t = ln.strip()
        if not t:
            continue

        bullet = bool(_BULLET.match(t))
        core = _LEAD.sub('', t).strip()

        sep = ':' if ':' in core else ('：' if '：' in core else None)
        head = core.split(sep, 1)[0].strip() if sep else ''
        who = _is_person(head) if sep else None

        if who:
            body = core.split(sep, 1)[1].strip()
            if not body:
                # B 寫法的人名標頭行，Goal 在底下的條列
                cur = who
                if who not in byname:
                    byname[who] = []
                    order.append(who)
                continue
            # A 寫法：同一行就有內容
            cur = who
            if '。/' in body:
                parts = [x.strip() for x in body.split('。/') if x.strip()]
                parts = [(p if p.endswith('。') else p + '。') for p in parts]
                warn.append({'code': 'AMBIGUOUS_GOAL_SEPARATOR', 'who': who,
                             'detail': '多個 Goal 寫在同一行、以 `。/` 分隔；依句號切開，'
                                       '但此寫法沒有硬邊界'})
            elif '/' in body:
                parts = [body]
                warn.append({'code': 'SLASH_WITHOUT_BOUNDARY', 'who': who,
                             'detail': '該行含 `/` 但無句號邊界，整行視為一個 Goal'})
            else:
                parts = [body]
            add(who, parts)
            continue

        if cur and bullet and core:
            # B 寫法的條列子項；`- 職缺管理 : xxx` 整行視為一個 Goal
            add(cur, [core])
            continue

        # 不是人名行也不是某人底下的條列 → Team Goal 區
        cur = None
        team.append(t)

    if not order:
        warn.append({'code': 'NO_PERSONAL_GOAL_PARSED', 'who': None,
                     'detail': '衝刺目標欄位裡找不到任何名單內的人名行（`姓名:` 或 '
                               '`N. 姓名：` 後接條列）。Personal Goal 為空，'
                               '02 區不會有任何 Goal 卡——這是資料問題不是「本期沒有 Goal」'})
    return team, [(n, byname[n]) for n in order], warn


# ── Goal → 卡號歸屬 ───────────────────────────────────────────────────
# Jira 目前沒有承載這件事的欄位（05 區的 1c 未決）。
# Sprint 14 的這份對應是 PO 口頭宣告後由本專案記錄的，**不是從 Jira 讀出來的**，
# 因此 source 標為 PO_DECLARED_NOT_IN_JIRA，並列入 mismatch。
# AI 不得用 label / Epic / 卡名 / description 語意推論歸屬。
GOAL_WORK_DECLARATIONS = {
    '8765': {
        'source': 'PO_DECLARED_NOT_IN_JIRA',
        'recorded_at': '2026-08-27',
        'goals': [
            {'gid': 'Q1', 'person': 'Quincy Chen', 'role': 'FE', 'seq': 0,
             'work': ['JOBHUB-826'], 'dependency': None, 'reconstructed': False,
             'theme': '面試管理'},
            {'gid': 'Q2', 'person': 'Quincy Chen', 'role': 'FE', 'seq': 1,
             'work': ['JOBHUB-402', 'JOBHUB-762', 'JOBHUB-825'], 'dependency': None,
             'reconstructed': True, 'theme': 'Bug / 優化'},
            {'gid': 'B1', 'person': 'Bill Wang', 'role': 'BE', 'seq': 0,
             'work': ['JOBHUB-771', 'JOBHUB-773', 'JOBHUB-774'], 'dependency': None,
             'reconstructed': False, 'theme': 'AI Tag'},
            {'gid': 'E1', 'person': 'Erica lh Lee', 'role': 'BE', 'seq': 0,
             'work': ['JOBHUB-770', 'JOBHUB-863'],
             'dependency': 'Erica → Quincy（下週串接）', 'reconstructed': False,
             'theme': '面試管理'},
            {'gid': 'L1', 'person': 'Lodifa Chen', 'role': 'QA', 'seq': 0,
             'work': ['JOBHUB-582', 'JOBHUB-861', 'JOBHUB-877'], 'dependency': None,
             'reconstructed': False, 'theme': '新手導覽',
             'non_team_goal_aligned': True},
        ],
        'team_goal_owner_map': [
            {'team_goal_index': 0, 'gids': ['B1']},
            {'team_goal_index': 1, 'gids': ['Q1', 'E1']},
            {'team_goal_index': 2, 'gids': ['Q2']},
        ],
        'participants': ['Quincy Chen', 'Bill Wang', 'Erica lh Lee', 'Lodifa Chen'],
        'non_participants': {'Heidi Tsai': 'PM', '陳語柔': 'External resource'},
    }
}


def load_goal_work_declaration(sid, sprint_name=None):
    """Goal → 卡號歸屬的來源，依序：

      1. `sprints/sprint-<n>/goalmap.json`（由 agent 從 JOBHUB-452 的
         `GOALMAP-V1` 留言落地，與 decision_comments.json 同一條路）
      2. 程式碼裡的 GOAL_WORK_DECLARATIONS（Sprint 14 的歷史宣告）

    兩者都沒有就回 None——看板必須明講「本期無歸屬來源」，
    **不得改用 label／Epic／卡名語意推論**。
    """
    try:
        from paths import sprint_dir
    except ImportError:
        from evidence.paths import sprint_dir
    p = _os.path.join(sprint_dir(sprint_name), 'goalmap.json')
    if _os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            d = _json.load(f)
        if d and d.get('goals'):
            d.setdefault('source', 'PO_DECLARED_VIA_JIRA_COMMENT')
            d.setdefault('team_goal_owner_map', [])
            d.setdefault('participants',
                         sorted({g['person'] for g in d['goals']}))
            d.setdefault('non_participants', {})
            return d
    return GOAL_WORK_DECLARATIONS.get(sid)


def build_layer_d(layer_a):
    sp = layer_a['sprint']
    sid = str(sp['id'])
    team_lines, personal_raw, warns = parse_sprint_goal(sp['goal_raw'])
    by_full = {ALIAS.get(n, n): sts for n, sts in personal_raw}
    unknown_names = [n for n, _ in personal_raw if n not in ALIAS]

    decl = load_goal_work_declaration(sid, sp.get('name'))
    if not decl:
        warns.append({'code': 'NO_GOAL_WORK_MAP', 'who': None,
                      'detail': 'Sprint %s 沒有 Goal→卡號歸屬來源（既無 '
                                'goalmap.json 也無程式碼宣告）。02 區不會有 Goal 卡，'
                                '時間軸沒有卡可以畫——這是缺 Layer D 輸入，'
                                '不是「本期沒有工作」' % sid})

    goals = []
    text_mismatch, text_missing, unmapped_text = [], [], []
    if decl:
        seen = {}
        for g in decl['goals']:
            i = seen.get(g['person'], 0)
            seen[g['person']] = i + 1
            sts = by_full.get(g['person'], [])
            entry = dict(g)
            if i < len(sts):
                entry['statement'] = sts[i]
                entry['statement_source'] = 'JIRA_SPRINT_GOAL_FIELD'
            else:
                entry['statement'] = None
                entry['statement_source'] = 'MISSING'
                text_missing.append(g['gid'])
            entry['work_source'] = decl['source']
            goals.append(entry)
        for p, sts in by_full.items():
            n = sum(1 for g in decl['goals'] if g['person'] == p)
            for extra in sts[n:]:
                unmapped_text.append({'person': p, 'statement': extra})

    return {
        'goal_field_raw': sp['goal_raw'],
        'team_goals': team_lines,
        'team_goals_source': 'JIRA_SPRINT_GOAL_FIELD',
        'personal_goal_statements': {k: v for k, v in by_full.items()},
        'personal_goal_source': 'JIRA_SPRINT_GOAL_FIELD',
        'goal_work_map_source': decl['source'] if decl else 'NONE',
        'goal_work_map_evaluable': bool(decl),
        'goal_work_map_note': (decl or {}).get('note', ''),
        'goals': goals,
        'team_goal_owner_map': decl['team_goal_owner_map'] if decl else [],
        # Participant ＝ 本 Sprint 在 Jira 衝刺目標欄位裡**有 Personal Sprint Goal 的人**。
        # 這是人在 Planning 宣告的，不是 AI 從 assignee 推的，所以沒有 goalmap 時
        # 仍然成立——02 區照樣列得出每個人的完整卡清單（全部進 Other Sprint Work），
        # 不會因為缺歸屬就整段消失。
        'participants': (decl['participants'] if decl
                         else list(by_full.keys())),
        'participants_source': ('GOAL_WORK_DECLARATION' if decl
                                else 'JIRA_SPRINT_GOAL_FIELD'),
        'non_participants': decl['non_participants'] if decl else {},
        'alias_map': ALIAS,
        'parse_warnings': warns,
        'unknown_goal_names': unknown_names,
        'goal_statement_missing': text_missing,
        'goal_statement_unmapped': unmapped_text,
    }
