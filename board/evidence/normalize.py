# -*- coding: utf-8 -*-
"""LAYER A · Raw Jira Fetch → canonical facts.

輸入（由 agent 以 Atlassian MCP 抓下來、原樣落地）：
  raw/issues_parent.json   searchJiraIssuesUsingJql 的回應（母卡）
  raw/issues_sub.json      同上（子任務）
  raw/changelog/all.json   逐張 getJiraIssue(expand=changelog) 正規化後的狀態轉換與日期寫入

輸出：一個 dict，只放**事實**。這一層不做任何判斷。
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')

# Jira 狀態 id → 語意角色。鍵在 id 而非名稱，因為
# fields.status.name 是中文、changelog 的 fromString/toString 是英文。
STATUS_ROLE = {
    '11784': 'BACKLOG',            # 待辦事項 / To Do
    '11785': 'ACTIVE',             # 進行中 / In Progress
    '11787': 'ACTIVE',             # 測試中 / Testing
    '11820': 'DELIVERY_COMPLETE',  # DEV DONE
    '11786': 'CLOSED',             # 完成 / Done
}
ROLE_ORDER = {'BACKLOG': 0, 'ACTIVE': 1, 'DELIVERY_COMPLETE': 2, 'CLOSED': 3}

# changelog 的 toString 是英文，用來在缺 id 時回填
NAME_TO_ID = {
    'To Do': '11784', '待辦事項': '11784',
    'In Progress': '11785', '進行中': '11785',
    'Testing': '11787', '測試中': '11787',
    'DEV DONE': '11820',
    'Done': '11786', '完成': '11786',
}


def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _nodes(payload):
    return payload['issues']['nodes']


def _date(v):
    """Jira 的日期欄位可能是 '2026-08-21' 或 '2026-08-21 00:00:00.0'。只取日期。"""
    if not v:
        return None
    return str(v)[:10]


def _sprint_of(fields, sprint_id):
    for s in (fields.get('customfield_10020') or []):
        if s.get('id') == sprint_id:
            return s
    return None


def build_layer_a(parent_path, sub_path, changelog_path, sprint_id):
    parents = _nodes(_load(parent_path))
    subs = _nodes(_load(sub_path))
    cl = _load(changelog_path)

    sprint = None
    for x in parents:
        s = _sprint_of(x['fields'], sprint_id)
        if s:
            sprint = {
                'id': s['id'], 'name': s['name'], 'state': s['state'],
                'boardId': s.get('boardId'),
                'goal_raw': s.get('goal') or '',
                'startDate': s.get('startDate'), 'endDate': s.get('endDate'),
                'completeDate': s.get('completeDate'),
            }
            break

    issues = {}
    for node, level in [(n, 'parent') for n in parents] + [(n, 'sub') for n in subs]:
        f = node['fields']
        k = node['key']
        st = f['status']
        entry = {
            'key': k,
            'summary': f.get('summary'),
            'level': level,
            'hierarchyLevel': (f.get('issuetype') or {}).get('hierarchyLevel'),
            'issuetype': (f.get('issuetype') or {}).get('name'),
            'status_id': st['id'],
            'status_name': st['name'],
            'status_role': STATUS_ROLE.get(st['id']),
            'assignee': ((f.get('assignee') or {}).get('displayName')) or None,
            'priority': ((f.get('priority') or {}).get('name')) or None,
            'parent': ((f.get('parent') or {}).get('key')) or None,
            'labels': f.get('labels') or [],
            'planned_start': _date(f.get('customfield_10015')),
            'planned_end': _date(f.get('duedate')),
            'in_sprint': bool(_sprint_of(f, sprint_id)),
            'issuelinks': [
                {
                    'type': (l.get('type') or {}).get('name'),
                    'inward_key': ((l.get('inwardIssue') or {}).get('key')),
                    'outward_key': ((l.get('outwardIssue') or {}).get('key')),
                }
                for l in (f.get('issuelinks') or [])
            ],
        }
        c = cl.get(k) or {}
        entry['transitions'] = [
            {
                'at': t['at'],
                'from_id': t.get('from_id') or NAME_TO_ID.get(t.get('from')),
                'to_id': t.get('to_id') or NAME_TO_ID.get(t.get('to')),
                'from_role': STATUS_ROLE.get(t.get('from_id') or NAME_TO_ID.get(t.get('from'))),
                'to_role': STATUS_ROLE.get(t.get('to_id') or NAME_TO_ID.get(t.get('to'))),
                'from': t.get('from'), 'to': t.get('to'),
            }
            for t in (c.get('transitions') or [])
        ]
        entry['date_writes'] = [
            {'at': w['at'], 'field': w['field'],
             'from': _date(w.get('from')), 'to': _date(w.get('to'))}
            for w in (c.get('date_writes') or [])
        ]
        entry['changelog_complete'] = (
            c.get('changelog_total') == c.get('changelog_returned')
            if c.get('changelog_total') is not None else None
        )
        issues[k] = entry

    return {'sprint': sprint, 'issues': issues}


if __name__ == '__main__':
    a = build_layer_a(
        os.path.join(RAW, 'issues_parent.json'),
        os.path.join(RAW, 'issues_sub.json'),
        os.path.join(RAW, 'changelog', 'all.json'),
        8765)
    print('sprint:', a['sprint']['name'], a['sprint']['startDate'], '→', a['sprint']['endDate'])
    print('issues:', len(a['issues']))
    print('with transitions:', sum(1 for v in a['issues'].values() if v['transitions']))
    print('with date_writes:', sum(1 for v in a['issues'].values() if v['date_writes']))
