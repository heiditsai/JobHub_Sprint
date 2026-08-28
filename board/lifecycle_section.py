# -*- coding: utf-8 -*-
"""CONDITIONAL SECTION SLOT —— Board 依 lifecycle_state 決定這一格放什麼。

版位固定：01 SPRINT OVERVIEW 之後、02 PERSONAL GOAL EXECUTION 之前。
四個狀態輪流佔用同一格，不會並存。**Board 既有 IA 一個字不改。**

SPRINT_CLOSURE 的版面刻意**沒有 freeze**（等 Sprint 14 validation run 後再裁），
這裡只做 plumbing：讀得到 state、找得到 decision、版位存在。
"""
import json, os

import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence'))
from paths import lifecycle_path as _lifecycle_path        # noqa: E402

LC = None
_p = _lifecycle_path()
if os.path.exists(_p):
    with open(_p, encoding='utf-8') as _f:
        LC = json.load(_f)

STATE_LABEL = {
    'NORMAL_EXECUTION': ('執行中', ''),
    'CLOSING_DECISION': ('T-2 · 收斂決策', 'lc-t2'),
    'FINAL_DAY_EXECUTION': ('T-1 · 最後一個工作日', 'lc-t1'),
    'SPRINT_CLOSURE': ('已收期', 'lc-closed'),
}

TAKEN_LABEL = {
    'NO_DECISION_YET': '尚未裁決',
    'HOLD_SCOPE': '守原 scope',
    'REDUCE_SCOPE': '縮小 scope',
    'CARRY_FORWARD': '明確 carry forward',
    'SUPERSEDED': '已被取代',
}


# 訊號 enum → 中文短標。卡片列已經是中文句子，這裡原本直接印 enum
# （OVERSIZED_PLANNED_DURATION 這種），同一件事在同一張看板上有兩種寫法。
SIG_LABEL = {
    'OVERDUE': '已逾期',
    'DUE_DATE_PASSED': '截止日已過',
    'DUE_TODAY': '今天到期',
    'DUE_TOMORROW': '明天到期',
    'DUE_IN_2_WORKING_DAYS': '剩 2 個工作天',
    'OVERSIZED_PLANNED_DURATION': '計畫工期過長·建議拆卡',
    'STARTED_LATE': '開工晚於計畫',
    'START_DELAY': '計畫開工日已過·尚未開工',
    'PLAN_EXTENDS_BEYOND_SPRINT': '計畫跨出本期',
    'STUCK_IN_DELIVERY_COMPLETE': '卡在 DEV DONE',
    'MISSING_ACTUAL_START_HISTORY': '有完成無開工紀錄',
}


def sig_label(s):
    """認得就給中文，不認得就照實印 enum——不要靜靜吞掉沒見過的訊號。"""
    return SIG_LABEL.get(s, s)


def _openlist(sc, limit=8):
    rows = sc['open_items'][:limit]
    more = len(sc['open_items']) - len(rows)
    out = ''.join(
        '<div class="lcrow"><span class="lck">%s</span>'
        '<span class="lcs">%s</span><span class="lcw">%s</span>'
        '<span class="lcsig">%s</span></div>'
        % (L(r['key']), esc(r['status']), esc(r['assignee'] or '未指派'),
           ''.join('<span class="tag warn">%s</span>' % esc(sig_label(s)) for s in r['signals'][:3]))
        for r in rows)
    if more > 0:
        out += '<div class="lcrow faint">…另有 %d 張未收</div>' % more
    return out


def render():
    if not LC:
        return
    lc = LC['lifecycle']
    st = lc['lifecycle_state']
    label, cls = STATE_LABEL[st]
    a = lc['anchors']

    # 每個狀態都先給一條 lifecycle 標記列（版位固定，內容隨 state 變）
    A('<div class="lcbar %s"><span class="lcstate">%s</span>'
      '<span class="lcq">%s</span>'
      '<span class="lcmeta">T-2 %s · T-1 %s · 剩 %d 個工作日 · evidence %s</span></div>'
      % (cls, esc(label), esc(lc['management_question']),
         a['second_last_working_day'], a['last_working_day'],
         lc['remaining_working_days'], LC['evidence']['fingerprint']))

    if st == 'NORMAL_EXECUTION':
        return                                   # 不長出任何 conditional section

    ds = LC['closing_decisions']

    # ── T-2 ──────────────────────────────────────────────────────────
    if st == 'CLOSING_DECISION':
        need = [d for d in ds if d['po_decision_required']]
        A('<div class="sec"><div class="sech"><span class="n">◆</span>'
          '<h2>CLOSING DECISIONS</h2>'
          '<span class="hint">PO DECISIONS REQUIRED · %d</span></div>' % len(need))
        if not ds:
            A('<div class="card pad"><b>No closing decision required.</b></div>')
        for d in ds:
            sc = d['scope_state']
            A('<div class="risk hi lcdec" id="%s"><div class="rh">'
              '<span class="who">%s</span><span class="mono faint">%s</span>%s'
              '<span class="tag">%s</span></div><dl>'
              % (d['decision_id'], esc(d['title']), d['decision_id'],
                 '<span class="tag bad">⚑ PO DECISION REQUIRED</span>'
                 if d['po_decision_required'] else
                 '<span class="tag">OWNER: %s</span>' % esc(d['owner']),
                 ' · '.join(d['goal_refs'])))
            A('<dt>WHAT WE KNOW</dt><dd>範圍 <b>%d</b> 張（含子卡）· 已完成 <b>%d</b>'
              '%s<div class="lclist">%s</div></dd>'
              % (sc['member_count'], sc['closed'],
                 ' · <b style="color:var(--red)">%d 張未指派</b>' % len(sc['unassigned'])
                 if sc['unassigned'] else '', _openlist(sc)))
            A('<dt>WHY NOW</dt><dd>%s</dd>' % esc(d['why_now']))
            if d.get('ask'):
                A('<dt class="you">ASK · %s</dt><dd class="you">%s</dd>'
                  % (esc(d['ask']['to']), esc(d['ask']['question'])))
            A('<dt>DECISION NEEDED</dt><dd>%s</dd>'
              % ' ／ '.join('<b>%s</b>' % TAKEN_LABEL[o] for o in d['options']))
            A('<dt>IF NO ACTION</dt><dd>%s</dd>' % esc(d['if_no_action']))
            A('<dt class="faint">裁決回填</dt><dd class="faint" style="font-size:11.5px">'
              '在 <a href="https://mayohumancapital.atlassian.net/browse/%s">%s</a> 留言貼上：'
              '<code>SPRINT-DECISION-V1 / decision_id: %s / decision_taken: '
              'HOLD_SCOPE｜REDUCE_SCOPE｜CARRY_FORWARD / acceptance_condition: …</code>'
              '（一行一個欄位）</dd>'
              % (LC['human_decision_source']['issue'],
                 LC['human_decision_source']['issue'], d['decision_id']))
            A('</dl></div>')

    # ── T-1 早上 ─────────────────────────────────────────────────────
    elif st == 'FINAL_DAY_EXECUTION':
        A('<div class="sec"><div class="sech"><span class="n">◆</span>'
          '<h2>FINAL DAY EXECUTION</h2>'
          '<span class="hint">昨天已裁決的事，今天不再問一次</span></div>')
        for d in ds:
            sc = d['scope_state']
            recorded = d['human_source'] == 'JIRA_DECISION_LOG'
            taken = d['decision_taken']
            A('<div class="risk%s lcdec" id="%s"><div class="rh">'
              '<span class="who">%s</span><span class="mono faint">%s</span></div><dl>'
              % ('' if taken != 'NO_DECISION_YET' else ' hi',
                 d['decision_id'], esc(d['title']), d['decision_id']))
            A('<dt>昨天的裁決</dt><dd>%s%s</dd>'
              % ('<b>%s</b>' % TAKEN_LABEL.get(taken, taken),
                 '　<span class="tag warn">未寫入裁決紀錄</span>' if not recorded
                 or taken == 'NO_DECISION_YET' else ''))
            if d.get('acceptance_condition'):
                A('<dt>ACCEPTANCE</dt><dd><b>%s</b></dd>' % esc(d['acceptance_condition']))
            A('<dt>CURRENT STATE</dt><dd>範圍 %d 張 · 已完成 %d'
              '<div class="lclist">%s</div></dd>'
              % (sc['member_count'], sc['closed'], _openlist(sc)))
            if taken == 'NO_DECISION_YET':
                A('<dt class="you">TODAY</dt><dd class="you">'
                  '昨天沒有留下裁決紀錄，因此今天無法把它轉成 execution focus。'
                  '<b>這不是重新分析——是缺少 acceptance condition。</b></dd>')
            else:
                A('<dt class="you">TODAY</dt><dd class="you">'
                  '依昨天的裁決執行；<b>PO 無需再次裁決</b>。</dd>')
            A('</dl></div>')

    # ── 收期後 ───────────────────────────────────────────────────────
    elif st == 'SPRINT_CLOSURE':
        A('<div class="sec"><div class="sech"><span class="n">◆</span>'
          '<h2>SPRINT CLOSURE</h2>'
          '<span class="hint">版面尚未定版 · 等 validation run 後裁決</span></div>')
        A('<div class="card pad"><div class="k">CLOSING DECISION FOLLOW-UP</div>'
          '<table><tr><th>ID</th><th>決策問題</th><th>裁決</th>'
          '<th>範圍完成</th><th>Leverage?</th></tr>%s</table>'
          '<div class="faint" style="font-size:11.5px;margin-top:10px">'
          'Leverage 一律 <code>HUMAN CONTEXT REQUIRED</code>：Jira 只能證明 Closing Decision '
          '之後發生了什麼，<b>不能單靠時間順序證明因果</b>。</div></div>'
          % ''.join(
              '<tr><td class="mono">%s</td><td>%s</td><td>%s</td>'
              '<td class="dim">%d／%d</td><td class="dim">HUMAN CONTEXT REQUIRED</td></tr>'
              % (d['decision_id'], esc(d['title']),
                 TAKEN_LABEL.get(d['decision_taken'], d['decision_taken']),
                 d['scope_state']['closed'], d['scope_state']['member_count'])
              for d in ds))

    # ── BEFORE NEXT SPRINT（T-2 起都顯示）────────────────────────────
    bns = LC.get('before_next_sprint') or []
    if bns and st in ('CLOSING_DECISION', 'FINAL_DAY_EXECUTION'):
        A('<div class="card pad" style="margin-top:10px"><div class="k">'
          'BEFORE NEXT SPRINT · %d</div>%s</div>' % (len(bns), ''.join(
              '<div class="lcrow" style="grid-template-columns:112px 1fr">'
              '<span class="lcw"><b>%s</b></span>'
              '<span>%s<div class="faint" style="font-size:11.5px">%s</div></span></div>'
              % (esc(b['owner']), esc(b['action']), esc(b['why'])) for b in bns)))

    if st != 'NORMAL_EXECUTION':
        A('</div>')


render()
