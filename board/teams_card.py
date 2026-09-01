# -*- coding: utf-8 -*-
"""把 evidence + lifecycle 轉成 Teams Adaptive Card（JSON 印到 stdout）。

    python3 teams_card.py > teams_card.json

**這支不負責發送。** webhook URL 是密鑰，不放 repo；POST 由排程那一端做。

它與看板共用同一份 evidence，所以兩邊不會各說各話。三條規則跟看板一致：
  * Goal → 卡號歸屬只用 Layer D 的人工宣告，**不從 label／Epic／卡名推論**
  * 不新增訊號，只把 evidence 已有的 enum 翻成中文（sig_labels.py）
  * 不比完成率、不排名、不判斷任何人的 performance
"""
import json, os, sys
from urllib.parse import quote as _urlquote

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence'))
from paths import evidence_path, lifecycle_path            # noqa: E402
from sig_labels import sig_label                           # noqa: E402

SITE = 'https://mayohumancapital.atlassian.net'
JIRA = SITE + '/browse/'
SNAPSHOT_URL = JIRA + 'JOBHUB-452'      # 快照存放卡，固定不變


def board_url(sprint):
    """Jira 看板網址由 sprint 自己的 boardId 推出來，不寫死。

    JOBHUB 是 team-managed（next-gen）專案，路徑**沒有** /c/ 這一段；
    company-managed 才有。boardId 拿不到時回專案首頁，不要給一個壞連結。
    """
    bid = (sprint or {}).get('boardId')
    if not bid:
        return SITE + '/jira/software/projects/JOBHUB/boards'
    return SITE + '/jira/software/projects/JOBHUB/boards/%s' % bid

STATE_LABEL = {
    'NORMAL_EXECUTION': '執行中',
    'CLOSING_DECISION': '倒數第二個工作日',
    'FINAL_DAY_EXECUTION': '最後一個工作日',
    'SPRINT_CLOSURE': '已收期',
}
ROLE_BUCKET = [
    ('ACTIVE', '🔄 進行中'),
    ('BACKLOG', '⬜ 還沒開始'),
    ('DELIVERY_COMPLETE', '🧩 已交付·等驗收'),
]
MAX_PER_BUCKET = 6          # Teams 卡片有 28KB 上限，超出的用「另有 N 張」帶過

# 團隊檔案庫裡當日 HTML 的固定位置（flow 寫檔，卡片先放連結）
#
# ⚠ 這個路徑含**空白**（Shared Documents）與**中文**（Daily看板），
# 直接拼進 Adaptive Card 的 url 會產生未編碼的 URL。Teams 的 Defender Safe Links
# 解析不了未編碼的 URL，點下去會停在 atp-safelinks.html 這張中繼頁而不轉址——
# 看起來像沒權限，其實是連結本身壞的。所以一律 percent-encode。
_FILES_BASE_RAW = ('https://huanuage.sharepoint.com/sites/msteams_12c4ef/'
                   'Shared Documents/Daily看板/')
FILES_BASE = _urlquote(_FILES_BASE_RAW, safe=':/')

# @ 提及用的公司帳號。**只有真的需要這個人今天處理時才 tag**（見 needs_action）。
# 查不到帳號的人一律不 tag——寧可漏，也不要 tag 錯人。
MENTION_UPN = {
    'Quincy Chen': 'quincy_chen@mayohr.com',
    'Bill Wang': 'bill_wang@mayohr.com',
    'Erica lh Lee': 'erica_lh_lee@mayohr.com',
    'Lodifa Chen': 'lodifa_chen@mayohr.com',
}

# 只有這幾種訊號算「需要本人今天處理」。清單刻意保持窄——
# 每天都被 tag 等於沒有 tag。
#
# 刻意不含 STUCK_IN_DELIVERY_COMPLETE：卡在 DEV DONE 代表開發已經交出去、
# 球在驗收端，tag 交付者是找錯人。那個數字改放在最上面的整體提醒裡。
ACTION_SIGNALS = {'OVERDUE', 'DUE_TODAY', 'DUE_TOMORROW', 'START_DELAY'}


# ── 小工具 ────────────────────────────────────────────────────────────
def tb(text, **kw):
    d = {'type': 'TextBlock', 'text': text, 'wrap': True}
    d.update(kw)
    return d


def note(text, style='warning'):
    return {'type': 'Container', 'style': style, 'spacing': 'medium',
            'items': [tb(text, weight='bolder')]}


def _short(s, n=58):
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + '…'


def line(iss, sigs):
    """一張卡一行：卡號、標題、訊號。子卡標「子」，未指派標紅。"""
    tag = '子 ' if iss['level'] == 'sub' else ''
    txt = '· %s**%s** %s' % (tag, iss['key'].replace('JOBHUB-', ''), _short(iss['summary']))
    s = sigs.get(iss['key']) or []
    if s:
        txt += '　_%s_' % '·'.join(sig_label(x) for x in s)
    if not iss.get('assignee'):
        txt += '　**未指派**'
    return txt


def bucket_text(items, sigs):
    rows = [line(i, sigs) for i in items[:MAX_PER_BUCKET]]
    more = len(items) - len(rows)
    if more > 0:
        rows.append('· …另有 %d 張' % more)
    return '\n\n'.join(rows)


# ── 主體 ──────────────────────────────────────────────────────────────
def needs_action(person, mine, sigs, open_dec):
    """這個人今天是否有需要他本人動作的事——是才 tag。

    回傳理由清單（空的代表不 tag）。判準只用既有訊號與既有的裁決 ask 對象，
    不新增判定、不做 performance 判斷。
    """
    why = []
    hit = sorted({sig_label(t) for i in mine
                  for t in (sigs.get(i['key']) or []) if t in ACTION_SIGNALS})
    if hit:
        why.append('·'.join(hit))
    for d in open_dec:
        if (d.get('ask') or {}).get('to') == person:
            why.append('%s 等你回答' % d['decision_id'])
    return why


def build(ev, lc, html_name=None):
    A = ev['layerA']['issues']
    A = A if isinstance(A, list) else list(A.values())
    B = ev['layerB']['derived']
    D = ev['layerD']
    L = lc['lifecycle']
    sigs = {k: [s['type'] for s in (v.get('signals') or [])] for k, v in B.items()}

    body = []
    body.append(tb('JobHub Sprint 執行看板', size='large', weight='bolder'))
    body.append(tb('%s · %s · 剩 **%d** 個工作天 · %s'
                   % (lc['sprint']['name'],
                      STATE_LABEL.get(L['lifecycle_state'], L['lifecycle_state']),
                      L['remaining_working_days'], L['today']),
                   isSubtle=True))

    # ── 今天最該知道的（有才長，沒有就不佔版面）────────────────────
    open_dec = [d for d in lc.get('closing_decisions', [])
                if d.get('decision_taken') in (None, 'NO_DECISION_YET')]
    if open_dec and L['lifecycle_state'] in ('CLOSING_DECISION', 'FINAL_DAY_EXECUTION'):
        body.append(note('🔴 %d 個收期裁決還沒有人拍板' % len(open_dec), 'attention'))
        rows = []
        for d in open_dec:
            row = '· **%s** %s' % (d['decision_id'], d['title'])
            ask = d.get('ask') or {}
            # 沒有指定要問誰就不要硬生一行「問 —：」出來
            if ask.get('to') and ask.get('question'):
                row += '　→ 問 %s：%s' % (ask['to'], _short(ask['question'], 70))
            rows.append(row)
        body.append(tb('\n\n'.join(rows), size='small'))

    unassigned = [i for i in A if not i.get('assignee')]
    if unassigned:
        body.append(note('🟡 %d 張卡沒有人承接' % len(unassigned)))
        body.append(tb(bucket_text(unassigned, sigs), size='small'))

    stuck = [k for k, v in sigs.items() if 'STUCK_IN_DELIVERY_COMPLETE' in v]
    overdue = [k for k, v in sigs.items() if 'OVERDUE' in v]
    if stuck or overdue:
        bits = []
        if stuck:
            bits.append('**%d 張**卡在 DEV DONE 兩個工作天以上（已交付、還沒被驗收）' % len(stuck))
        if overdue:
            bits.append('**%d 張**已逾期' % len(overdue))
        body.append(note('🟡 ' + '；'.join(bits)))

    # ── 每個人（點名字展開）────────────────────────────────────────
    body.append(tb('每個人（點名字展開）', size='medium', weight='bolder', spacing='medium'))
    entities = []
    goals_by_person = {}
    for g in D.get('goals', []):
        goals_by_person.setdefault(g['person'], []).append(g)

    for idx, person in enumerate(D.get('participants', [])):
        mine = [i for i in A if i.get('assignee') == person]
        cnt = {r: [i for i in mine if i.get('status_role') == r] for r, _ in ROLE_BUCKET}
        summary = ' · '.join('%s %d' % (lab.split(' ')[-1], len(cnt[r]))
                             for r, lab in ROLE_BUCKET)
        why = needs_action(person, mine, sigs, open_dec)
        upn = MENTION_UPN.get(person)
        if why and upn:
            name_txt = '<at>%s</at>' % person
            entities.append({'type': 'mention', 'text': name_txt,
                             'mentioned': {'id': upn, 'name': person}})
        else:
            name_txt = '**%s**' % person
        cid = 'p%d' % idx
        body.append({
            'type': 'ColumnSet', 'spacing': 'small', 'separator': True,
            'selectAction': {'type': 'Action.ToggleVisibility', 'targetElements': [cid]},
            'columns': [
                {'type': 'Column', 'width': 'stretch',
                 'items': [tb(name_txt + ('　⚠ %s' % why[0] if why else '')),
                           tb('%s 張 · %s' % (len(mine), summary), isSubtle=True, size='small')]},
                {'type': 'Column', 'width': 'auto', 'items': [tb('▾')]},
            ]})

        inner = []
        for g in goals_by_person.get(person, []):
            inner.append(tb('🎯 %s' % g['statement'], size='small', spacing='small'))
            if g.get('dependency'):
                inner.append(tb('↳ 宣告相依：%s' % g['dependency'], size='small', isSubtle=True))
        for r, lab in ROLE_BUCKET:
            if cnt[r]:
                inner.append(tb(lab, weight='bolder', size='small', spacing='small'))
                inner.append(tb(bucket_text(cnt[r], sigs), size='small'))
        if not inner:
            inner.append(tb('本期名下沒有卡片。', size='small', isSubtle=True))
        body.append({'type': 'Container', 'id': cid, 'isVisible': False, 'items': inner})

    body.append(tb('Goal → 卡號歸屬為 PO 人工宣告（Jira 無此欄位），看板不從 label／Epic／卡名推論。'
                   '訊號與日期取自 changelog，Jira 沒填就標未填、不回推。',
                   size='small', isSubtle=True, spacing='medium'))

    card = {'type': 'AdaptiveCard', 'version': '1.2', 'msTeams': {'width': 'full'},
            'body': body,
            'actions': [
                {'type': 'Action.OpenUrl', 'title': 'Jira Sprint 看板',
                 'url': board_url(ev['layerA'].get('sprint'))},
                {'type': 'Action.OpenUrl', 'title': '每日快照 JOBHUB-452', 'url': SNAPSHOT_URL},
            ]}
    if html_name:
        card['actions'].insert(0, {'type': 'Action.OpenUrl', 'title': '今天的完整看板',
                                   'url': FILES_BASE + _urlquote(html_name)})
    if entities:
        # 提及實體必須放在 msteams（小寫）；msTeams 那個是版面寬度，兩者不同鍵
        card['msteams'] = {'entities': entities}
    return card


def main():
    # 用法：python3 teams_card.py [看板.html]
    # 帶檔案時 payload 會多一個 file 區塊，讓 Power Automate 自己把它寫進團隊檔案庫，
    # 並在卡片上多一顆「今天的完整看板」按鈕。
    html_path = sys.argv[1] if len(sys.argv) > 1 else None
    html_name = os.path.basename(html_path) if html_path else None
    with open(evidence_path(), encoding='utf-8') as f:
        ev = json.load(f)
    with open(lifecycle_path(), encoding='utf-8') as f:
        lc = json.load(f)
    card = build(ev, lc, html_name)
    payload = {
        # 舊 flow 直接轉發整包也還能運作，先留著這兩個鍵
        'type': 'message',
        'attachments': [{'contentType': 'application/vnd.microsoft.card.adaptive',
                         'content': card}],
        # 新 flow 用這兩個
        'card': card,
    }
    if html_path:
        with open(html_path, encoding='utf-8') as f:
            payload['file'] = {'name': html_name, 'content': f.read()}
    out = json.dumps(payload, ensure_ascii=False)
    sys.stdout.write(out)
    sys.stderr.write('card %d bytes（Teams 上限 28KB）· payload %d bytes\n'
                     % (len(json.dumps(card, ensure_ascii=False).encode()), len(out.encode())))


if __name__ == '__main__':
    main()
