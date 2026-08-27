# -*- coding: utf-8 -*-
"""LAYER D · Human Input.

只放**人明確宣告過**的東西，並且每一項都必須帶 source。
AI 不得在這一層做任何語意推論。
"""

ALIAS = {"Quincy": "Quincy Chen", "Bill": "Bill Wang",
         "Erica": "Erica lh Lee", "Lodifa": "Lodifa Chen"}


def parse_sprint_goal(raw):
    """Jira 衝刺目標欄位 → (team_lines, [(alias, [statement,...])], warnings)

    規則（保守，寧可標示模稜兩可也不猜）：
      一行一個 Goal，格式 `姓名:一句話`；同姓名多行 ＝ 多個 Goal。
      相容寫法：同一行用 `。/` 分隔——**只認句號＋斜線**，
      因為單純的 `/` 會和內文（例如「Bug / 優化」）撞在一起。
    """
    team, order, byname, warn = [], [], {}, []
    for ln in (raw or '').split('\n'):
        t = ln.strip()
        if not t:
            continue
        sep = ':' if ':' in t else ('：' if '：' in t else None)
        head = t.split(sep, 1)[0].strip() if sep else ''
        if sep and head and not head[0].isdigit() and len(head) <= 12:
            body = t.split(sep, 1)[1].strip()
            if '。/' in body:
                parts = [x.strip() for x in body.split('。/') if x.strip()]
                parts = [(p if p.endswith('。') else p + '。') for p in parts]
                warn.append({'code': 'AMBIGUOUS_GOAL_SEPARATOR', 'who': head,
                             'detail': '多個 Goal 寫在同一行、以 `。/` 分隔；依句號切開，'
                                       '但此寫法沒有硬邊界'})
            elif '/' in body:
                parts = [body]
                warn.append({'code': 'SLASH_WITHOUT_BOUNDARY', 'who': head,
                             'detail': '該行含 `/` 但無句號邊界，整行視為一個 Goal'})
            else:
                parts = [body]
            if head not in byname:
                byname[head] = []
                order.append(head)
            byname[head] += parts
        else:
            team.append(t)
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


def build_layer_d(layer_a):
    sp = layer_a['sprint']
    sid = str(sp['id'])
    team_lines, personal_raw, warns = parse_sprint_goal(sp['goal_raw'])
    by_full = {ALIAS.get(n, n): sts for n, sts in personal_raw}
    unknown_names = [n for n, _ in personal_raw if n not in ALIAS]

    decl = GOAL_WORK_DECLARATIONS.get(sid)

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
        'goals': goals,
        'team_goal_owner_map': decl['team_goal_owner_map'] if decl else [],
        'participants': decl['participants'] if decl else [],
        'non_participants': decl['non_participants'] if decl else {},
        'alias_map': ALIAS,
        'parse_warnings': warns,
        'unknown_goal_names': unknown_names,
        'goal_statement_missing': text_missing,
        'goal_statement_unmapped': unmapped_text,
    }
