# -*- coding: utf-8 -*-
# SECTION 05 · DATA CONTRACT — 分兩層：一次性前置作業 + 每週例行
nod_all = [m for m in M if not m['pstart'] and not m['pend']]
skip_all = sorted(NO_INPROGRESS)
dd_all = [m for m in M if m['st'] == 'devdone']

A('<div class="sec"><div class="sech"><span class="n">05</span>'
  '<h2>要讓這張看板說真話，需要做什麼</h2>'
  '<span class="hint">每一項都直接對應到上面某個「無法判定」</span></div>')

A('<div class="banner" style="border-color:var(--bd);background:var(--tint);margin:0 0 14px">'
  '<div class="t">分兩層：先做<b>一次性前置作業</b>，每週例行才有地方落。</div>'
  '<div class="b">下面第一張表的六件事沒做完，第二張表的五個習慣就算團隊照做，'
  '看板也讀不到。<b>2026-08-27 已解決其中最大的一項</b>：Personal Sprint Goal 定案寫在 '
  '<b>Jira 衝刺目標欄位</b>，本看板的 Goal 文字已改為每天從那裡讀、逐字呈現。'
  '剩下的缺口是<b>「哪幾張卡支撐哪個 Goal」還沒有地方放</b>——那部分目前仍為人工提供。</div></div>')

# ── 一次性前置作業 ───────────────────────────────────────────────
A('<div class="card"><div class="pad" style="padding-bottom:6px">'
  '<div style="font-size:11px;letter-spacing:.1em;color:var(--tx3);margin-bottom:9px">'
  'A · 一次性前置作業（做完才輪到每週例行）</div></div><div class="scroll"><table>'
  '<tr><th style="width:26px"></th><th style="width:250px">要建立什麼</th>'
  '<th style="width:92px">誰</th><th style="width:110px">什麼時候</th>'
  '<th>沒有它會怎樣</th></tr>')

SETUP = [
 ("1", "<b>決定 Personal Sprint Goal 存在哪裡</b><br>"
       "<span class='faint' style='font-size:11.5px'>已定案：寫在 <b>Jira 衝刺目標欄位</b>，"
       "編號那幾行是 Team Goal，底下 <code>姓名:一句話</code> 是 Personal Goal</span>",
       "PM", "已完成<br>2026-08-27",
       "<b>02 區的 Goal 文字已改為每天從 Jira 讀，不再人工轉錄。</b>"
       "<span class='tag ok'>已定案並已寫入</span>"),
 ("1b", "<b>把「一行一個 Goal」訂成寫法</b><br>"
       "<span class='faint' style='font-size:11.5px'>同一人有多個 Goal 就重複寫兩行 "
       "<code>姓名:…</code>，不要用 <code>/</code> 串在同一行</span>",
       "PM", "Sprint 15<br>Planning 之前",
       "本期 Quincy 的兩個 Goal 寫在同一行、用 <code>/</code> 分隔，"
       "而句子內文本身就含 <code>/</code>（「Bug / 優化」）。"
       "看板目前靠<b>句號＋斜線</b>才切得開——這個邊界不可靠，"
       "換個人寫法不同就會解析錯。"
       "<span class='tag warn'>目前：靠句號推斷</span>"),
 ("1c", "<b>決定 Goal → 卡號的歸屬存在哪裡</b><br>"
       "<span class='faint' style='font-size:11.5px'>Goal 文字有地方放了，"
       "但「哪幾張卡支撐這個 Goal」還沒有</span>",
       "PM", "Sprint 15<br>Planning 之前",
       "<b>這是目前唯一還靠人工提供的環節。</b>沒有它，看板知道每個人承諾什麼、"
       "卻不知道哪些卡在支撐它——所有卡都會落進「Other Sprint Work」，"
       "而看板<b>不會替任何人猜</b>。"
       "<span class='tag bad'>目前：人工提供</span>"),
 ("2", "<b>決定哪幾張是 Goal Critical</b><br>"
       "<span class='faint' style='font-size:11.5px'>建議：goal owner 在自己的 SG 卡上列 2–3 個卡號</span>",
       "每個人", "Planning 當天",
       "Goal Health 只能退回「完成幾張卡」。<b>4／5 完成但最後一張是 API 串接，Goal 仍然是 At Risk</b>——"
       "沒有 critical 標記就分不出這件事。"),
 ("3", "<b>不要從 To Do 直接跳 DEV DONE</b><br>"
       "<span class='faint' style='font-size:11.5px'>已定案：<b>口頭約定，不改 Jira workflow</b></span>",
       "PM 口頭<br>告知工程", "已處理<br>2026-08-27",
       "Actual Start 是從 <code>To Do → In Progress</code> 讀的。跳過這一階的卡算不出開工時間，"
       "<b>依賴開工時間的判定（開工晚了／計畫日開工至今未動）對它失效</b>；"
       "到期、逾期、停在 DEV DONE 這類仍然算得出來。<br>"
       "口頭約定沒有系統擋，所以<b>看板每期都會數一次還有幾張跳階</b>，"
       "數字降不下來就代表約定沒生效、需要改用 workflow 限制。"
       "<span class='tag warn'>本期基準：%d 張跳階（%s）</span>"
       % (len(skip_all), '、'.join(k[7:] for k in skip_all))),
 ("4", "<b>把 <code>Flagged</code> 放到卡片畫面上，並公告它就是求救管道</b>",
       "PM / Jira", "本週內",
       "04 區每一條「在等什麼」都只能靠讀留言猜。"
       "<span class='tag bad'>目前：全期 0 張設過</span>"),
 ("5", "<b>確認 <code>issuelinks</code> 的「is blocked by」可用並教一次</b>",
       "PM", "本週內",
       "看板畫不出「A 擋住 B」——不是不會畫，是<b>沒有邊可畫</b>。"
       "<span class='tag bad'>目前：期內 0 條相依邊</span>"),
 ("6", "<b>決定 Planning Freeze 要不要鎖</b><br>"
       "<span class='faint' style='font-size:11.5px'>Sprint 開始後改計畫日期：留痕即可，還是禁止？</span>",
       "PM", "Sprint 15 前",
       "不鎖的話，任何人都可以在週四把 <code>duedate</code> 改成週五，"
       "<b>plan vs actual 永遠好看</b>。本看板已改為偵測寫入時間並標 BACKDATED，但那是事後補救。"),
]
for n, what, who, when, why in SETUP:
    A('<tr><td class="faint mono">%s</td><td>%s</td><td class="dim">%s</td>'
      '<td class="dim">%s</td><td class="dim">%s</td></tr>' % (n, what, who, when, why))
A('</table></div>')

# ── 每週例行 ────────────────────────────────────────────────────
A('<div class="pad" style="border-top:1px solid var(--line);padding-bottom:6px">'
  '<div style="font-size:11px;letter-spacing:.1em;color:var(--tx3);margin-bottom:9px">'
  'B · 每週例行（每個人）</div></div><div class="scroll"><table>'
  '<tr><th style="width:26px"></th><th style="width:250px">你要做的</th>'
  '<th style="width:110px">什麼時候</th><th>不做的話，看板會變成什麼樣</th>'
  '<th style="width:170px">現在的實況</th></tr>')

HABITS = [
 ("1", "寫下自己的 <b>Personal Sprint Goal</b>，並指認支撐它的卡號",
       "Planning 當天",
       "你的卡全部落進「Other Sprint Work」，看板不會替你猜它們屬於哪個目標。",
       '<span class="tag ok">Goal 文字已入 Jira</span><br>'
       '<span class="tag bad">卡號歸屬仍為人工</span>'),
 ("2", "替本期要做的每張卡壓上 <code>Start date</code> 與 <code>duedate</code>",
       "Planning 當天<br><b>不是開工當天</b>",
       "卡排不進時間軸，<b>而且永遠不會逾期</b>。Sprint 開始後才填＝事後回填，"
       "拿來算 Plan vs Actual 只會得到「一切正常」。",
       '<span class="tag bad">%d／%d 張沒壓起迄日</span><br>'
       '<span class="tag warn">Goal Work 只有 3／12 的計畫日期早於 Sprint</span>'
       % (len(nod_all), len(M))),
 ("3", "開工時把卡從 <code>To Do</code> 拉到 <code>In Progress</code>",
       "真的開始做的那一刻",
       "看板算不出你什麼時候開始，<b>「晚幾天開工」整條失效</b>。"
       "（已口頭約定，Jira 沒有系統限制，靠自律。）",
       '<span class="tag warn">本期 %d 張跳階</span>' % len(skip_all)),
 ("4", "卡住時把 <code>Flagged</code> 設成 <code>Impediment</code>，"
       "並用 <code>issuelinks</code> 登記被誰擋住",
       "當下，不要等 Daily",
       "你在等的東西沒有人看得見。04 區只能靠讀留言推測，而推測會漏。",
       '<span class="tag bad">全期 0 張</span>'),
 ("5", "<code>DEV DONE</code> 不是終點——驗完轉 <code>Done</code>；"
       "母卡收掉前先看子卡",
       "交付與驗收時",
       "DEV DONE 會被誤讀成完成。母卡標完成但子卡還在動，Goal 看起來達成、實際上有尾巴。",
       '<span class="tag bad">402 停在 DEV DONE 15 個工作天</span><br>'
       '<span class="tag warn">582 母卡已完成，子卡 728 仍進行中</span>'),
]
for n, what, when, cost, now in HABITS:
    A('<tr><td class="faint mono">%s</td><td><b>%s</b></td><td class="dim">%s</td>'
      '<td class="dim">%s</td><td>%s</td></tr>' % (n, what, when, cost, now))
A('</table></div>')

# ── 每人缺口 ────────────────────────────────────────────────────
A('<div class="pad" style="border-top:1px solid var(--line);padding-bottom:6px">'
  '<div style="font-size:11px;letter-spacing:.1em;color:var(--tx3);margin-bottom:9px">'
  'C · 你自己的缺口（只列缺的，不列做對的）</div></div><div class="scroll"><table>'
  '<tr><th style="width:140px">人</th><th style="width:80px">母卡</th>'
  '<th style="width:230px">沒壓起迄日</th><th>其他</th></tr>')
for w in PARTICIPANTS:
    cs = [m for m in M if m['who'] == w]
    nod = [m['key'] for m in cs if not m['pstart'] and not m['pend']]
    skip = [k for k in skip_all if (BY.get(k) or {}).get('who') == w]
    stuck = [m['key'] for m in cs if m['st'] == 'devdone']
    ex = []
    if skip: ex.append('跳過 In Progress：%s' % '、'.join(k[7:] for k in skip))
    if stuck: ex.append('停在 DEV DONE：%s' % '、'.join(k[7:] for k in stuck))
    if w == "Bill Wang": ex.append('774 底下 5 張子卡無人承接（811–815）')
    if w == "Lodifa Chen": ex.append('582 母卡已關但子卡 728 未完')
    ratio = len(nod) / len(cs) if cs else 0
    badge = ('<span class="tag bad">%d／%d</span>' % (len(nod), len(cs))) if ratio > .5 else \
            (('<span class="tag warn">%d／%d</span>' % (len(nod), len(cs))) if nod else '<span class="tag ok">0</span>')
    A('<tr><td><b>%s</b></td><td class="dim">%d 張</td>'
      '<td>%s <span class="faint" style="font-size:11px">%s</span></td>'
      '<td class="dim" style="font-size:12px">%s</td></tr>'
      % (esc(w), len(cs), badge, ' '.join(k[7:] for k in nod), '<br>'.join(ex) or '—'))
A('</table></div>')
A('<div class="pad" style="padding-top:12px"><div class="faint" style="font-size:11.5px">'
  '這一區<b>只列缺口</b>。當 C 表變成空的、A 表六項做完，01 區的 Sprint Health 才會開始有值——'
  '在那之前它會一直是「無法判定」，而不是拿其他數字頂替。</div></div>')
A('</div></div>')
