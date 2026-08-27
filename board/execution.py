# -*- coding: utf-8 -*-
# SECTION 02 · PERSONAL GOAL EXECUTION —— 承諾 × 執行 × 時間，同一張表
DIDX = {dt: i for i, (dt, _, _) in enumerate(DAYS)}


def span(a_, b_):
    if not a_ or not b_: return None
    if b_ < DAYS[0][0] or a_ > DAYS[-1][0]: return None
    ai = DIDX.get(a_, 0 if a_ < DAYS[0][0] else 4)
    bi = DIDX.get(b_, 0 if b_ < DAYS[0][0] else 4)
    return max(0, min(ai, 4)), max(0, min(bi, 4))


def bars_of(k):
    m = BY.get(k) or SBY[k]; cl = CL.get(k); bc = baseline_class(k)
    ps, pe = d(m['pstart']), d(m['pend'])
    a0, a1 = (d(cl[0]), d(cl[2])) if cl else (None, None)
    if not a1 and a0: a1 = TODAY
    return (span(ps, pe) if bc == "PLANNED" else None), span(a0, a1)


def card_row(k, kind, gid=None):
    """一張卡一列：狀態、偏差、計畫起迄、日期風險、plan/actual 條"""
    m = BY.get(k) or SBY[k]
    tags, _ = dev_of(k)
    sp, sa = bars_of(k)
    late = any('tag bad' in t for t in tags)
    badge = ('<span class="tag plan">%s</span>' % gid) if kind == 'goal' else \
            ('<span class="tag">OTHER</span>' if kind == 'other' else '<span class="tag">子卡</span>')
    risk = plan_risk(k)
    ds = (m['pstart'] or '')[5:].replace('-', '/')
    de_ = (m['pend'] or '')[5:].replace('-', '/')
    cl = CL.get(k)
    act = ''
    if cl:
        f = lambda x: x[5:].replace('-', '/') if x and x != '—' else '—'
        act = '<span class="mono faint"> · 實 %s→%s</span>' % (f(cl[0]), f(cl[2]))
        if k in NO_INPROGRESS:
            act += '<span class="faint">（未經 In Progress）</span>'
    A('<div class="erow">')
    A('<div class="c-work">%s %s <span class="wt">%s</span>'
      '<div class="wmeta">%s%s</div>%s</div>'
      % (badge, L(k), esc(m['sum']), stat(k), act,
         ('<div class="wrisk">%s</div>' % ' '.join(tags)) if tags else ''))
    A('<div class="c-date%s">%s%s</div>'
      % ('' if has_dates(k) else ' none',
         ('%s → %s' % (ds or '—', de_ or '—')) if has_dates(k) else '未填起迄日',
         ('<span class="why">⚑ %s</span>' % esc(risk)) if risk else ''))
    for i, (dt, _, _) in enumerate(DAYS):
        A('<div class="cell%s" style="grid-column:%d"></div>' % (' td' if dt == TODAY else '', i + 3))
    A('<div class="lane">')
    if sp: A('<div class="bar p" style="grid-column:%d/%d"></div>' % (sp[0] + 1, sp[1] + 2))
    if sa: A('<div class="bar a%s" style="grid-column:%d/%d"></div>' % (' late' if late else '', sa[0] + 1, sa[1] + 2))
    A('</div></div>')
    # 子卡 roll-up
    kids = sorted(SUB.get(k, []), key=lambda y: y['key'])
    if kids:
        kd = sum(1 for x in kids if x['st'] == 'done')
        whoc = collections.Counter(x['who'] for x in kids)
        whos = ' · '.join('%s %d' % (w2, c) for w2, c in whoc.most_common())
        warn = ''
        if whoc.get('未指派'): warn += ' <span class="tag bad">%d 張無人承接</span>' % whoc['未指派']
        dv = sum(1 for x in kids if x['st'] == 'devdone')
        if dv: warn += ' <span class="tag warn">%d 張停在 DEV DONE</span>' % dv
        A('<div class="erow"><div class="full sub"><details><summary class="subsum">'
          '↳ 子卡 <b>%d／%d</b> 完成　<span class="faint">%s</span>%s</summary>'
          '<div class="scroll"><table class="subtbl">%s</table></div></details></div></div>'
          % (kd, len(kids), whos, warn,
             ''.join('<tr><td style="width:104px">%s</td><td>%s%s</td>'
                     '<td style="width:110px">%s</td><td style="width:126px" class="dim">%s</td></tr>'
                     % (L(x['key']), esc(x['sum']),
                        (('<br><span class="faint" style="font-size:11px">📌 %s</span>'
                          % esc(KEY_SUBS[x['key']]['why'])) if x['key'] in KEY_SUBS else '')
                        + (('<div class="wrisk">%s</div>' % ' '.join(dev_of(x['key'])[0]))
                           if dev_of(x['key'])[0] else ''),
                        stat(x['key']),
                        esc(x['who']) if x['who'] != '未指派' else '<b style="color:var(--red)">未指派</b>')
                     for x in kids)))


A('<div class="sec"><div class="sech"><span class="n">02</span>'
  '<h2>PERSONAL GOAL EXECUTION</h2>'
  '<span class="hint">承諾 · 執行 · 時間 —— 同一張表</span></div>')

nodate_all = [m for m in M if not m['pstart'] and not m['pend']]
A('<div class="banner" style="border-left-color:var(--amb);margin:0 0 12px">'
  '<div class="t">⚑ 35 張卡裡有 <b>%d 張沒壓起迄日</b>（%.0f%%），它們永遠不會在 Jira 上逾期</div>'
  '<div class="b">沒有 <code>Start date</code>／<code>duedate</code> 的卡排不進時間軸，也不會觸發任何逾期判定。'
  '分布：%s。<br>下表是<b>每個 participant 的完整清單</b>——Goal Work、Other Sprint Work 一張卡一行，不省略；'
  '子卡收在母卡底下可展開。</div></div>'
  % (len(nodate_all), len(nodate_all) / len(M) * 100,
     ' · '.join('%s <b>%d</b>' % (w, c) for w, c in
                sorted(collections.Counter(m['who'] for m in nodate_all).items(), key=lambda x: -x[1]))))

A('<div class="card"><div class="scroll escroll"><div class="egrid">')
# 欄位表頭
A('<div class="erow hdr"><div class="c-work">WORK · STATUS · SIGNAL</div>'
  '<div class="c-date">計畫起迄日<span class="why" style="color:var(--tx3);font-weight:600">'
  '⚑ ＝ 這個日期有問題</span></div>%s</div>'
  % ''.join('<div class="c-day%s" style="grid-column:%d">%s（%s）%s</div>'
            % (' td' if dt == TODAY else '', i + 3, lab, w,
               '<br>TODAY' if dt == TODAY else ('<br>15:00 收期' if dt == SPRINT['end'] else ''))
            for i, (dt, lab, w) in enumerate(DAYS)))

for person in PARTICIPANTS:
    gs = [g for g in GOALS if g['person'] == person]
    gw = [k for g in gs for k in g['work']]
    other = [m['key'] for m in M if m['who'] == person and m['key'] not in gw]
    mysubs = [x for x in S if x['who'] == person]
    nod = sum(1 for m in M if m['who'] == person and not m['pstart'] and not m['pend'])
    tot_p = len(gw) + len(other)
    goal_lines = []
    for g in gs:
        done = sum(1 for k in g['work'] if (BY.get(k) or SBY[k])['st'] == 'done')
        _lv, _lab, _why = goal_health(g)
        health = '<span class="hs %s">%s</span>' % (_lv, esc(
            {'red': '紅燈 · %s' % _why.replace(' 亮紅燈', ''),
             'unknown': '無紅燈 · 判定不足',
             'ok': '完成'}[_lv]))
        goal_lines.append(
            '<div class="gline"><span class="tag plan gidt">%s</span>'
            '<span class="gtx">%s</span>%s'
            '<span class="gmeta">%d／%d 完成　%s</span></div>'
            % (g['gid'], esc(g['statement']),
               ' <span class="tag warn">事後重建</span>' if g['reconstructed'] else '',
               done, len(g['work']), health))
        if g['dep']:
            goal_lines.append('<div class="gline dep">↳ 宣告相依：%s</div>' % esc(g['dep']))
    A('<div class="erow"><div class="full pname" id="%s">'
      '<div class="ptop"><span class="pn">%s</span><span class="prole">%s</span>'
      '<span class="pstat">Goal Work %d · Other %d · 名下子卡 %d／%d · '
      '<b style="color:var(--amb)">%d 張沒壓起迄日</b></span></div>%s</div></div>'
      % (anchor_of(person), esc(person), gs[0]['role'], len(gw), len(other),
         sum(1 for x in mysubs if x['st'] == 'done'), len(mysubs), nod,
         ''.join(goal_lines)))

    for g in gs:
        for k in g['work']:
            card_row(k, 'goal', g['gid'])

    if other:
        A('<div class="erow"><div class="full divhd">OTHER SPRINT WORK · %d 張'
          '<span class="dvn">未對應到已宣告的 Personal Goal。本看板<b>不推論</b>它們屬於哪個 Goal——'
          '為什麼這張卡在 Sprint 裡，但不支撐這個人這週宣告要達成的事？</span></div></div>' % len(other))
        for k in other:
            card_row(k, 'other')

    if mysubs:
        fo = [x for x in mysubs if BY.get(x['parent']) and BY[x['parent']]['who'] != person]
        if fo:
            byp = collections.OrderedDict()
            for x in sorted(fo, key=lambda y: y['key']): byp.setdefault(x['parent'], []).append(x)
            A('<div class="erow"><div class="full divhd">你名下的子卡，掛在別人的母卡底下 · %d 張'
              '<span class="dvn">這些工作<b>不會計入你的母卡完成率</b>——以母卡為單位的報表會漏掉它們。</span>'
              '%s</div></div>'
              % (len(fo),
                 ''.join('<details style="margin:6px 0 0"><summary class="subsum">'
                         '↳ %d 張在 %s（%s 的母卡）</summary>'
                         '<div class="scroll"><table class="subtbl">%s</table></div></details>'
                         % (len(xs), L(p), esc(BY[p]['who']),
                            ''.join('<tr><td style="width:104px">%s</td><td>%s</td>'
                                    '<td style="width:110px">%s</td></tr>'
                                    % (L(x['key']), esc(x['sum']), stat(x['key'])) for x in xs))
                         for p, xs in byp.items())))

A('</div></div>')
A('<div class="pad" style="border-top:1px solid var(--line)">'
  '<div class="faint" style="font-size:11.5px;line-height:1.85">'
  '<span class="bar p" style="display:inline-block;width:26px;vertical-align:middle"></span> 計畫'
  '（<b>只在計畫日期可比對時畫</b>）　'
  '<span class="bar a" style="display:inline-block;width:26px;vertical-align:middle"></span> 實際　'
  '<span class="bar a late" style="display:inline-block;width:26px;vertical-align:middle"></span> 實際・有偏差<br>'
  '<b>⏰ ＝ 截止日狀態</b>：剩 2 個工作天／明天到期／今天到期／已逾期。'
  '這是<b>事實陳述，不論日期何時寫入都會標</b>；但「逾期幾天」只在計畫日期可比對時才給數字。<br>'
  '<b>✂ ＝ 計畫工期超過 %d 個工作天</b>，建議拆成更小的卡——'
  '一張橫跨多天的卡在時間軸上只會是一條長條，中間卡住看不出來，'
  '拆開後每一段都有自己的截止日與交付物。<b>看板不代為決定怎麼拆。</b><br>'
  '<b>事後補填 / 未填起迄日 的卡不畫計畫線</b>——畫出來只會製造「照計畫走」的假象。'
  '有些卡沒壓起迄日但右邊仍有藍色實際線，那就是「有做但沒排」。<br>'
  '完全落在本週之外的卡（例如 08/06 就做完的）沒有可畫的區段，但仍然一行一張列在這裡。</div></div>'
  % SPLIT_DAYS)
A('</div></div>')
