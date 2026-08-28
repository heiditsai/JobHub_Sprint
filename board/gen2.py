# -*- coding: utf-8 -*-
import html, collections, os, sys
from datetime import date, timedelta
exec(open('data3.py',encoding='utf-8').read())

# 輸出檔名不寫死：比照 evidence/paths.py 的慣例（環境變數優先，其次由資料推導）
#   1. 命令列第一個參數
#   2. 環境變數 BOARD_OUT
#   3. jobhub-sprint-execution-<evidence as_of>.html
def out_path():
    if len(sys.argv) > 1 and sys.argv[1]:
        return sys.argv[1]
    env = os.environ.get('BOARD_OUT')
    if env:
        return env
    return 'jobhub-sprint-execution-%s.html' % TODAY.isoformat()

BASE="https://mayohumancapital.atlassian.net/browse/"
def esc(s): return html.escape(str(s))
def L(k): return '<a href="%s%s">%s</a>'%(BASE,k,k)
O=[]; A=O.append

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--tx:#111;--tx2:#5b5a56;--tx3:#8d8b85;--line:#e4e3dc;
--bd:rgba(17,17,17,.11);--blue:#2a6fd6;--red:#c8342f;--amb:#8a6100;--grn:#0a6b33;
--ok:#e9f2ea;--warn:#fdf3e0;--bad:#fdecea;--tint:#eef3fa;--track:#e9e8e2}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0d0d0d;--card:#191918;--tx:#fff;
--tx2:#bdbcb3;--tx3:#84837b;--line:#2b2b29;--bd:rgba(255,255,255,.13);--blue:#4a90e8;--red:#e8706a;
--amb:#f0b23a;--grn:#38b866;--ok:#152418;--warn:#2a2213;--bad:#2b1615;--tint:#16212f;--track:#262623}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:14px/1.55 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
.w{max-width:1660px;margin:0 auto;padding:22px 20px 70px}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
h1{font-size:20px;margin:0;letter-spacing:-.01em}
.sec{margin:30px 0 0}
.sech{display:flex;align-items:baseline;gap:12px;border-bottom:2px solid var(--tx);padding-bottom:6px;margin-bottom:14px}
.sech .n{font:600 11px/1 system-ui;letter-spacing:.14em;color:var(--tx3)}
.sech h2{font-size:15px;margin:0;letter-spacing:.02em}
.sech .hint{margin-left:auto;font-size:12px;color:var(--tx3)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:8px}
.pad{padding:14px 16px}
.top{display:flex;flex-wrap:wrap;align-items:baseline;gap:14px;border-bottom:1px solid var(--line);padding-bottom:12px}
.chip{font-size:12px;color:var(--tx2);border:1px solid var(--bd);border-radius:5px;padding:2px 8px}
.chip.now{border-color:var(--blue);color:var(--blue);font-weight:600}
table{border-collapse:collapse;width:100%;font-size:13px}
th{text-align:left;font-weight:600;font-size:11px;letter-spacing:.06em;color:var(--tx3);
 padding:7px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:0}
.scroll{overflow-x:auto}
.mono{font-variant-numeric:tabular-nums}
.st{display:inline-block;font-size:12px;white-space:nowrap}
.dim{color:var(--tx2)}.faint{color:var(--tx3)}
.nod{color:var(--amb);font-weight:600;font-size:11px}
.subrow td{padding:0 10px 6px;border-bottom:1px solid var(--line)}
.subsum{padding:5px 0;font-size:12px;color:var(--tx2);list-style:none}
.subsum::-webkit-details-marker{display:none}
.subsum:hover{color:var(--tx)}
details[open]>.subsum{color:var(--tx);font-weight:600;border-bottom:0}
.subtbl{background:var(--bg);border-radius:6px;margin:4px 0 8px}
.subtbl td{padding:5px 10px;font-size:12px;border-bottom:1px solid var(--line)}
.subtbl tr:last-child td{border-bottom:0}
.bad-t{color:var(--red)}
.tag{display:inline-block;font-size:10.5px;letter-spacing:.04em;padding:1px 6px;border-radius:4px;
 border:1px solid var(--bd);color:var(--tx2);white-space:nowrap}
.tag.bad{border-color:var(--red);color:var(--red);background:var(--bad)}
.tag.warn{border-color:var(--amb);color:var(--amb);background:var(--warn)}
.tag.ok{border-color:var(--grn);color:var(--grn);background:var(--ok)}
.tag.plan{border-color:var(--blue);color:var(--blue);background:var(--tint)}
/* overview */
.ov{display:grid;grid-template-columns:1.02fr 1.62fr .92fr;gap:12px;margin-top:12px;align-items:stretch}
.ov>.card{display:flex;flex-direction:column}
.gid2{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.03em;padding:0 5px;
 border:1px solid var(--bd);border-radius:4px;color:var(--tx2);vertical-align:1px}
.tgr{display:flex;gap:12px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line);font-size:12.5px}
.tgr:first-of-type{border-top:0;padding-top:2px}
.tgr .tgl{flex:1;line-height:1.5}
.tgr .tgo{flex:none;font-size:11.5px;color:var(--tx2);text-align:right;white-space:nowrap}
.tgr.out{border-top:1px dashed var(--bd);margin-top:3px;padding-top:8px}
.pgl{display:flex;flex-direction:column;margin-top:1px}
.pgr{display:grid;grid-template-columns:30px 54px 1fr auto;gap:9px;align-items:baseline;
 padding:8px 8px 8px 9px;font-size:12.5px;color:var(--tx);text-decoration:none;
 border-left:2px solid var(--line);border-bottom:1px solid var(--line)}
.pgr:last-child{border-bottom:0}
.pgr:hover{background:var(--bg);text-decoration:none}
.pgr.red{border-left-color:var(--red)}
.pgr.unknown{border-left-color:var(--tx3)}
.pgr.ok{border-left-color:var(--grn)}
.pgr .pgw{font-weight:650}
.pgr .pgt{line-height:1.5;color:var(--tx2)}
.pgr .hs{font-size:11.5px;white-space:nowrap;font-weight:600}
.pgr.red .hs{color:var(--red)}
.pgr.unknown .hs{color:var(--tx3);font-weight:400}
.pgr.ok .hs{color:var(--grn)}
.hlist{margin-top:9px;font-size:12px;line-height:1.75}
.hlist .r{padding:2px 0}
.hlist .r{display:flex;gap:8px;align-items:baseline}
.hlist .r .g{font-weight:650;color:var(--red);flex:none;white-space:nowrap}
.hlist .r .c{color:var(--tx2)}
.spacer{flex:1}
.note{font-size:11px;color:var(--tx3);line-height:1.65;margin-top:10px;
 padding-top:9px;border-top:1px solid var(--line)}
@media(max-width:900px){.ov{grid-template-columns:1fr}}
.ov .k{font-size:11px;letter-spacing:.1em;color:var(--tx3);margin-bottom:7px}
.big{font-size:22px;font-weight:650;letter-spacing:-.01em;line-height:1.2}
.big.bad{color:var(--red)}.big.warn{color:var(--amb)}
.tg{white-space:pre-line;font-size:13.5px;line-height:1.75}
.banner{background:var(--card);border:1px solid var(--bd);border-left:3px solid var(--red);
 border-radius:6px;padding:11px 15px;margin-top:12px}
.banner .t{font-weight:650;margin-bottom:3px;font-size:13px}
.banner .b{font-size:12.5px;color:var(--tx2);line-height:1.75}
/* goal */
.gl{margin:12px 0 0}
.glh{display:flex;align-items:baseline;gap:10px;padding:11px 16px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.glh .nm{font-weight:650;font-size:15px}
.glh .ro{font-size:11px;color:var(--tx3);letter-spacing:.08em}
.glh .rt{margin-left:auto;font-size:12px;color:var(--tx2)}
.gbody{padding:0 16px 14px}
.goal{border-top:1px solid var(--line);padding:13px 0 4px}
.goal:first-child{border-top:0}
.goal .gt{font-size:10.5px;letter-spacing:.1em;color:var(--tx3)}
.goal .gs{font-size:14px;font-weight:600;margin:3px 0 8px;line-height:1.5}
.goal .gd{font-size:12px;color:var(--amb);margin:-4px 0 8px}
.hl{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--tx2);margin-bottom:9px}
.hl b{color:var(--tx)}
/* timeline */
.tl{display:grid;grid-template-columns:288px 118px 104px repeat(5,1fr);font-size:12px;min-width:1160px}
.tl .h{padding:6px 8px;color:var(--tx3);font-size:11px;border-bottom:1px solid var(--line)}
.tl .h.td{color:var(--blue);font-weight:600}
.trow{display:grid;grid-template-columns:288px 118px 104px repeat(5,1fr);min-width:1160px;
 border-bottom:1px solid var(--line);position:relative}
.trow .lab{padding:7px 8px;font-size:12px}
.trow .bl{padding:7px 6px;text-align:center}
.cell{border-left:1px solid var(--line);grid-row:1;position:relative}
.trow .lab{grid-column:1;grid-row:1}
.trow .bl{grid-column:3;grid-row:1}
.cell.td{background:rgba(42,111,214,.055)}
.lane{grid-column:4/-1;grid-row:1;display:grid;grid-template-columns:repeat(5,1fr);
 gap:3px;padding:7px 0;align-content:center}
.bar{height:9px;border-radius:5px;position:relative}
.bar.p{background:var(--track);border:1px solid var(--bd)}
.bar.a{background:var(--blue)}
.bar.a.late{background:var(--red)}
.brow{display:contents}
.pl{font-size:10px;color:var(--tx3);padding-left:8px}
.pl2{color:var(--tx3)}
.tl .h.ns{border-left:1px solid var(--line);border-right:2px solid var(--line)}
.tl .h.dh{border-left:1px solid var(--line)}
.dt{grid-column:2;grid-row:1;padding:7px 8px;font-size:11px;text-align:center;
 border-left:1px solid var(--line)}
.dt.none{color:var(--amb);font-weight:600;
 background:repeating-linear-gradient(135deg,transparent,transparent 6px,var(--line) 6px,var(--line) 7px)}
.nsc{grid-column:3;grid-row:1;padding:7px 6px;text-align:center;border-left:1px solid var(--line);
 border-right:2px solid var(--line)}
.owner{font-weight:650;font-size:13px;padding:12px 8px 4px;grid-column:1/-1;border-top:2px solid var(--line)}

.lcbar{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-top:14px;
 padding:9px 14px;border:1px solid var(--bd);border-left:3px solid var(--tx3);
 border-radius:6px;background:var(--card);font-size:12.5px}
.lcbar.lc-t2{border-left-color:var(--amb)}
.lcbar.lc-t1{border-left-color:var(--red)}
.lcbar.lc-closed{border-left-color:var(--grn)}
.lcbar .lcstate{font-weight:700;letter-spacing:.02em}
.lcbar .lcq{color:var(--tx2)}
.lcbar .lcmeta{margin-left:auto;color:var(--tx3);font-size:11px;font-variant-numeric:tabular-nums}
.risk.lcdec dl{grid-template-columns:132px 1fr}
.lclist{margin-top:6px;border-top:1px solid var(--line);padding-top:5px}
.lcrow{display:grid;grid-template-columns:104px 92px 112px 1fr;gap:4px 10px;
 align-items:baseline;padding:3px 0;font-size:12px;border-top:1px solid var(--line)}
.lcrow:first-child{border-top:0}
.lcrow .lck{font-variant-numeric:tabular-nums}
.lcrow .lcs{color:var(--tx2)}
.lcrow .lcw{color:var(--tx2)}
.lcrow .lcsig{display:flex;gap:4px;flex-wrap:wrap}

/* execution grid */
.egrid{min-width:1598px}
.erow{display:grid;grid-template-columns:460px 118px 214px repeat(5,1fr);min-width:1598px;
 border-bottom:1px solid var(--line)}
.c-work{grid-column:1;grid-row:1;padding:9px 12px;font-size:12.5px;line-height:1.5}
.c-work .wt{color:var(--tx)}
.c-work .wmeta{color:var(--tx2);font-size:11.5px;margin-top:3px;display:flex;flex-wrap:wrap;gap:4px;align-items:center}
.c-work .wrisk{margin-top:5px;display:flex;flex-wrap:wrap;gap:5px;align-items:center}
/* 開發狀態：獨立一欄，不再擠在 WORK 欄的 meta 行裡 */
.c-dev{grid-column:2;grid-row:1;padding:9px 8px;font-size:12px;line-height:1.5;
 border-left:1px solid var(--line)}
.c-dev .st{white-space:normal}
.c-dev .devwho{display:block;margin-top:3px;font-size:11px;color:var(--tx3)}
.c-dev .devwho.none{color:var(--red);font-weight:700}
.c-date{grid-column:3;grid-row:1;padding:9px 8px;font-size:11px;text-align:center;
 border-left:1px solid var(--line);border-right:2px solid var(--line);
 font-variant-numeric:tabular-nums}
.c-date.none{color:var(--amb);font-weight:600;
 background:repeating-linear-gradient(135deg,transparent,transparent 6px,var(--line) 6px,var(--line) 7px)}
.c-date .why{display:block;margin-top:3px;font-size:10px;line-height:1.4;color:var(--amb);font-weight:600}
.c-day{grid-row:1;padding:7px 8px;font-size:11px;color:var(--tx3);border-left:1px solid var(--line)}
.c-day.td{color:var(--blue);font-weight:600}
.erow.hdr>div{font-size:11px;letter-spacing:.05em;color:var(--tx3);font-weight:600;
 padding-top:8px;padding-bottom:8px}
.erow.hdr{border-bottom:0;background:var(--card);position:sticky;top:0;z-index:6;
 box-shadow:0 2px 0 var(--tx),0 6px 10px -8px rgba(0,0,0,.35)}
/* 窄視窗：卡片內橫向捲動（此時 sticky 失效，但版面不會破）
   寬視窗：不建立捲動容器，表頭才能 sticky 貼在視窗頂端 */
.escroll{overflow-x:auto}
@media(min-width:1660px){.escroll{overflow:visible}}
.egrid .cell{border-left:1px solid var(--line);grid-row:1}
.egrid .cell.td{background:rgba(42,111,214,.055)}
.egrid .lane{grid-column:4/-1;grid-row:1;display:grid;grid-template-columns:repeat(5,1fr);
 grid-template-rows:9px 9px;gap:5px 3px;padding:10px 0;align-content:center}
.egrid .lane .bar.p{grid-row:1}
.egrid .lane .bar.a{grid-row:2}
.full{grid-column:1/-1;grid-row:1;padding:0}
.pname{scroll-margin-top:56px;padding:14px 14px 12px;border-top:2px solid var(--tx);background:var(--bg)}
.pname .prole{font-size:11px;color:var(--tx3);letter-spacing:.08em;margin-left:6px}
.pname .pstat{margin-left:auto;font-size:11.5px;font-weight:400;color:var(--tx2)}
.pname .ptop{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.pname .pn{font-weight:650;font-size:15.5px}
.gline{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-top:6px;
 font-size:12.5px;font-weight:400;padding-left:2px}
.gline .gidt{flex:none}
.gline .gtx{font-weight:600;color:var(--tx)}
.gline .gmeta{margin-left:auto;color:var(--tx2);font-size:11.5px;display:flex;gap:12px;align-items:baseline}
.hs{font-size:11.5px;white-space:nowrap;font-weight:600}
.hs.red{color:var(--red)}
.hs.unknown{color:var(--tx3);font-weight:400}
.hs.ok{color:var(--grn)}
.gline.dep{color:var(--amb);font-size:11.5px;padding-left:34px;margin-top:2px}
.divhd{padding:11px 14px;background:var(--bg);font-size:12.5px;font-weight:600}
.divhd .dvn{display:block;font-weight:400;font-size:11.5px;color:var(--tx2);margin-top:3px}
/* 子卡：走母卡同一條 timeline —— 巢狀 .erow 沿用同一組 grid-template-columns，
   欄位左右對齊母卡，日期格與 lane 落在同樣的五天上 */
.full.sub{padding:0}
.subwrap{background:var(--bg);border-top:1px solid var(--line)}
.erow.subr{border-bottom:1px solid var(--line);background:var(--bg)}
.erow.subr:last-child{border-bottom:0}
.erow.subr .c-work{padding-left:32px;font-size:12px;position:relative}
.erow.subr .c-work .sarr{position:absolute;left:14px;top:9px;color:var(--tx3)}
.erow.subr .c-dev,.erow.subr .c-date{font-size:11px}
.erow.subr .lane{padding:7px 0}
.erow.subr .bar{height:7px}
.subsum .sn{margin-left:6px;color:var(--tx3);font-size:11.5px}
/* risk */
.risk{border:1px solid var(--bd);border-left:3px solid var(--amb);border-radius:6px;padding:12px 15px;margin:9px 0;background:var(--card)}
.risk.hi{border-left-color:var(--red)}
.risk{scroll-margin-top:20px}
.risk .rh{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:7px}
.risk .who{font-weight:650}
.risk dl{display:grid;grid-template-columns:92px 1fr;gap:5px 12px;margin:0;font-size:12.5px}
.risk dt{color:var(--tx3);font-size:10.5px;letter-spacing:.06em;padding-top:2px;white-space:nowrap}
.risk dd{margin:0;color:var(--tx2)}
.risk dd b{color:var(--tx)}
.risk dt.you{color:var(--red);font-weight:700}
.risk dt.you.soft{color:var(--tx2);font-weight:600}
.risk dd.you{color:var(--tx);font-weight:600}
.risk .yr{grid-column:1/-1;height:1px;background:var(--line);margin:5px 0 3px}
details{margin:8px 0}
summary{cursor:pointer;font-size:13px;padding:9px 14px;color:var(--tx2)}
summary:hover{color:var(--tx)}
details[open]>summary{color:var(--tx);font-weight:600;border-bottom:1px solid var(--line)}
.foot{margin-top:32px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--tx3)}
code{font-family:ui-monospace,Menlo,monospace;font-size:.92em;background:var(--tint);padding:0 4px;border-radius:3px}
"""

# ── 計算 ────────────────────────────────────────────────────────────
def has_dates(k):
    m=BY.get(k) or SBY.get(k)
    return bool(m and (m['pstart'] or m['pend']))

def plan_risk(k):
    """這張卡的日期有什麼風險——沒有風險就回空字串，不佔版面"""
    if not has_dates(k):
        return ''          # 斜線格本身就是說明，22 張卡不需要重複同一句話
    bc=baseline_class(k)
    if bc=="PLANNED": return ''
    note=(CL.get(k) or (None,None,None,None,''))[4]
    if bc=="BACKDATED":
        return note or '開工後才寫入，延遲判定不成立'
    return note or ''

SPLIT_DAYS = 3   # 計畫工期超過幾個工作天就建議拆卡

def dev_of(k):
    """回傳 (list of tag html, 偏差是否可判定)"""
    m=BY.get(k) or SBY.get(k); cl=CL.get(k); bc=baseline_class(k)
    tags=[]
    ps,pe=d(m['pstart']),d(m['pend'])
    a0,a1=(d(cl[0]),d(cl[2])) if cl else (None,None)
    ok=(bc=="PLANNED")            # 計畫日期可比對，偏差才算得準
    done=(m['st']=='done')

    # (1) 工期過長 → 建議拆卡。看的是計畫值本身，與日期何時寫入無關
    if ps and pe and not done:
        dur=wd(ps,pe)+1
        if dur>SPLIT_DAYS:
            tags.append('<span class="tag warn">&#9986; 計畫工期 %d 個工作天 · 建議拆成更小的卡</span>'%dur)

    # (2) 截止日狀態 → 事實陳述，不論日期何時寫入都標
    if pe and not done:
        v=wd(TODAY,pe)
        if v<0:
            if ok:
                tags.append('<span class="tag bad">&#9200; 已逾期 %d 個工作天</span>'%(-v))
            elif m['st']!='devdone':
                tags.append('<span class="tag bad">&#9200; 截止日 %s 已過，尚未完成</span>'%pe.strftime('%m/%d'))
        elif v==0:
            tags.append('<span class="tag bad">&#9200; 今天到期，尚未完成</span>')
        elif v==1:
            tags.append('<span class="tag bad">&#9200; 明天到期，尚未完成</span>')
        elif v==2:
            tags.append('<span class="tag warn">&#9200; 剩 2 個工作天</span>')

    # (3) 開工偏差 → 只有計畫日期可比對時才算得出來
    if ok:
        if a0 and ps and a0>ps:
            tags.append('<span class="tag bad">開工晚了 %d 個工作天</span>'%wd(ps,a0))
        if not a0 and ps and ps<TODAY and m['st']=='todo':
            tags.append('<span class="tag bad">計畫 %s 開工，至今未動</span>'%ps.strftime('%m/%d'))
        if pe and pe>SPRINT['end']:
            tags.append('<span class="tag">計畫跨出本期</span>')

    # (4) 卡在 DEV DONE
    if m['st']=='devdone' and cl and cl[1] and cl[1]!='—':
        dd=wd(d(cl[1]),TODAY)
        if dd and dd>=2:
            tags.append('<span class="tag bad">停在 DEV DONE %d 個工作天</span>'%dd)
    return tags, ok

GBY={g['gid']:g for g in GOALS}

def goal_health(g):
    """(level, 標籤html, 一句話理由)。red = 有卡片亮紅燈；unknown = 沒紅燈但判定基礎不足"""
    ks=g['work']
    reds=[k for k in ks if 'tag bad' in ''.join(dev_of(k)[0])]
    ncmp=sum(1 for k in ks if baseline_class(k)=="PLANNED")
    done=sum(1 for k in ks if (BY.get(k) or SBY[k])['st']=='done')
    if reds:
        why='%s 亮紅燈'%('、'.join(k[7:] for k in reds))
        return 'red','<span class="tag bad">&#9888; 已出現紅燈</span>',why
    if done==len(ks):
        return 'ok','<span class="tag ok">&#9679; 卡片全數完成</span>','%d／%d 完成'%(done,len(ks))
    if ncmp==0:
        return 'unknown','<span class="tag">— 無紅燈，但無法判定偏差</span>','%d 張卡的計畫日期不可比對或沒填'%len(ks)
    if ncmp<len(ks):
        return 'unknown','<span class="tag">— 無紅燈，部分無法判定</span>','只有 %d／%d 張日期可比對'%(ncmp,len(ks))
    return 'ok','<span class="tag ok">&#9679; 無已確認偏差</span>','%d／%d 完成'%(done,len(ks))

def anchor_of(person):
    return 'p%d'%PARTICIPANTS.index(person)

def stat(k):
    m=BY.get(k) or SBY.get(k)
    return '<span class="st">%s %s</span>'%(ICON[m['st']],STL[m['st']])

def pa(k):
    m=BY.get(k) or SBY.get(k); cl=CL.get(k)
    def f(x): return x[5:].replace('-','/') if x and x!='—' else '—'
    ps=f(m['pstart']); pe=f(m['pend'])
    a0=f(cl[0]) if cl else '—'; a1=f(cl[2]) if cl else '—'
    extra=' <span class="faint">（未經 In Progress）</span>' if k in NO_INPROGRESS else ''
    return ('<span class="mono faint">計 %s→%s</span><br><span class="mono">實 %s→%s</span>%s'
            %(ps,pe,a0,a1,extra))

# ══ HTML ══════════════════════════════════════════════════════════
A('<title>JobHub Sprint 執行看板</title>')
A('<style>%s</style>'%CSS)
A('<div class="w">')

# ── header ──
A('<div class="top"><h1>JobHub Sprint 執行看板</h1>'
  '<span class="chip">SPRINT 14</span><span class="chip">Aug 24 – Aug 28 15:00</span>'
  '<span class="chip now">Today · 週四 · Day 4 / 5</span>'
  '<span class="chip">%d issues in sprint</span>'
  '<span style="margin-left:auto" class="faint">資料 2026-08-27 16:05 · Jira changelog + fields</span></div>'%len(M))

# ── SECTION 1 ──
A('<div class="sec"><div class="sech"><span class="n">01</span><h2>SPRINT OVERVIEW</h2>'
  '<span class="hint">這個 Sprint 還能不能成功</span></div>')
A('<div class="ov">')

HL={g['gid']:goal_health(g) for g in GOALS}
reds=[g for g in GOALS if HL[g['gid']][0]=='red']
unks=[g for g in GOALS if HL[g['gid']][0]=='unknown']

# ── 卡1 · TEAM SPRINT GOAL（含 Personal Goal 覆蓋關係）──
tg_rows=[]
for line,gids in TEAM_GOAL_MAP:
    owners=[]
    for gid in gids:
        g=GBY[gid]; lv,_lab,_why=HL[gid]
        dot={'red':'var(--red)','unknown':'var(--tx3)','ok':'var(--grn)'}[lv]
        owners.append('<a href="#%s"><span class="gid2" style="border-color:%s;color:%s">%s</span>'
                      '</a> %s%s'%(anchor_of(g['person']),dot,dot,gid,esc(g['person'].split()[0]),
                                   '<span class="faint">（事後重建）</span>' if g['reconstructed'] else ''))
    tg_rows.append('<div class="tgr"><div class="tgl">%s</div><div class="tgo">%s</div></div>'
                   %(esc(line),' · '.join(owners) if owners else
                     '<span class="tag bad">無人宣告</span>'))
out=[GBY[x] for x in OUTSIDE_TEAM_GOAL]
A('<div class="card pad"><div class="k">TEAM SPRINT GOAL → 誰扛</div>%s'
  '<div class="tgr out"><div class="tgl faint">不在本期 Team Goal 內</div><div class="tgo">%s</div></div>'
  '<div class="faint" style="font-size:11px;margin-top:9px">'
  '團隊目標與個人目標<b>同一個來源</b>：Jira 衝刺目標欄位。'
  '本卡取編號那幾行；下一張卡取 <code>姓名:一句話</code> 那幾行。'
  '哪個 Goal 支撐哪條團隊目標，是各人宣告時自己標的，<b>非 AI 推論</b>。</div></div>'
  %(''.join(tg_rows),
    ' · '.join('<a href="#%s"><span class="gid2">%s</span></a> %s'
               %(anchor_of(g['person']),g['gid'],esc(g['person'].split()[0])) for g in out)))

# ── 卡2 · PERSONAL SPRINT GOALS 逐條 ──
rows=[]
for g in GOALS:
    lv,lab,why=HL[g['gid']]
    short={'red':'紅燈 · %s'%why.replace(' 亮紅燈',''),
           'unknown':'無紅燈 · 判定不足',
           'ok':'完成'}[lv]
    rows.append('<a class="pgr %s" href="#%s"><span class="gid2">%s</span>'
                '<span class="pgw">%s</span>'
                '<span class="pgt">%s</span><span class="hs">%s</span></a>'
                %(lv,anchor_of(g['person']),g['gid'],esc(g['person'].split()[0]),
                  esc(g['statement']),esc(short)))
A('<div class="card"><div class="pad" style="padding-bottom:4px">'
  '<div class="k">PERSONAL SPRINT GOALS · %d 條</div></div>'
  '<div class="pgl">%s</div>'
  '<div class="pad" style="padding-top:9px"><div class="faint" style="font-size:11px">'
  '逐字取自 <b>Jira 衝刺目標欄位</b>，看板不改寫。點一下跳到那個人的執行明細。%s</div></div></div>'
  %(len(GOALS),''.join(rows),
    ''.join('<br><span style="color:var(--amb)">⚑ %s</span>'%w for w in GOAL_PARSE_WARN)))

# ── 卡3 · SPRINT HEALTH ──
A('<div class="card pad"><div class="k">SPRINT HEALTH</div>'
  '<div class="big%s" style="font-size:19px">%d／%d 個 Goal<br>已出現紅燈</div>'
  '<div class="hlist">%s</div>'
  '<div class="dim" style="font-size:12px;margin-top:7px">'
  '另有 <b>%d 條</b>無紅燈但判定基礎不足（%s）。</div>'
  '<div class="spacer"></div>'
  '<div class="note">紅燈＝卡片已亮紅色訊號：逾期、到期未完成、'
  '停在 DEV DONE、開工晚了。<br>「判定不足」是偏差算不出來，不代表安全。</div></div>'
  %(' bad' if reds else '',len(reds),len(GOALS),
    ''.join('<div class="r"><span class="g">%s %s</span>'
            '<span class="c">%s</span></div>'
            %(g['gid'],esc(g['person'].split()[0]),HL[g['gid']][2]) for g in reds),
    len(unks),'、'.join(g['gid'] for g in unks) or '無'))
A('</div>')

A('<div class="banner"><div class="t">⚑ 紅燈之外的盲區：12 張 Goal Work 只有 3 張的計畫日期可以拿來比對</div>'
  '<div class="b">我們用 Jira changelog 檢查每一張 Goal Work 的「計畫日期是什麼時候被寫進 Jira 的」：'
  '<b>只有 %s、%s、%s</b>（都是 Bill 的 AI Tag 線，08-18 Planning 當天填）的計畫日早於執行。'
  '其餘 5 張是<b>事後回填</b>、4 張<b>從未填過</b>。'
  '典型：%s 的計畫日在卡片進 DEV DONE 之後 <b>13 天</b>才寫；'
  '%s 的計畫日與 DEV DONE <b>同一分鐘</b>寫入；'
  '%s 的截止日在開工前 <b>4 秒</b>寫入。'
  '這種日期拿來算 Plan vs Actual 只會得到「一切正常」。'
  '<b>影響範圍：紅燈照常算得出來</b>——到期未完成、逾期、停在 DEV DONE 都是狀態事實；'
  '算不出來的是「比計畫晚了幾天」這類偏差量。所以上面那 1 條「無紅燈但無法判定」'
  '不等於安全，只是<b>連燈都亮不起來</b>。</div></div>'
  %(L("JOBHUB-771"),L("JOBHUB-773"),L("JOBHUB-774"),L("JOBHUB-402"),L("JOBHUB-825"),L("JOBHUB-863")))
A('</div>')

exec(open('lifecycle_section.py',encoding='utf-8').read())

exec(open('execution.py',encoding='utf-8').read())

# ── SECTION 4 · NEEDS ATTENTION ──
RISKS=[
 dict(hi=True, who="Bill Wang", key="JOBHUB-771", type="OVERDUE · 計畫日期可比對",
   signal="計畫 08/19→08/21（08-18 Planning 當天填，可比對）・實際 08/19 開工・現況 In Progress",
   cause="12 張子卡只剩 <b>JOBHUB-787</b> 一張待辦，卡上零留言、無外部依賴",
   impact="逾期 <b>4 個工作天</b>。它是 Bill 的 Goal「使 PM 與 QA 可以測試」的前置，也是本期唯一一張<b>計畫日期早於執行、因此延遲可被判定</b>的卡",
   act="Bill 今天回報 787 還要多久", you="裁決：787 留在本期做完，或明講它移出", heidi=True),
 dict(hi=True, who="Bill Wang", key="JOBHUB-774", type="STARTED LATE · 無人承接",
   signal="計畫 08/24→08/31（08-18 Planning 當天填，可比對）・實際 <b>今天 11:48</b> 才開工",
   cause="五張子卡 811–815 至今無指派人，其中 811、815 是 P0",
   impact="晚 <b>3 個工作天</b>開工，母卡截止 08/31＝下週一。Goal 承諾「PM 與 QA 可以測試」的可測平台就在這張",
   act="Bill 提出 811–815 的承接人選", you="裁決：補人指派，或把可測範圍縮到 08/28 交得出來的", heidi=True),
 dict(hi=True, who="Erica lh Lee → Quincy Chen", key="JOBHUB-866", type="CROSS-PERSON DEPENDENCY",
   signal="Erica 的 Goal 明寫「使 Quincy 下週可以串接」。實際交付物是 866（契約＋mock，FE 解鎖點）・<b>今天 10:00 才開工</b>・無截止日",
   cause="866 是 863 的子卡，母卡 863 的截止日 09/02 已跨出本期",
   impact="Quincy 下週能不能開始串接，取決於這張今天才開工、且沒有承諾日的子卡",
   act="Erica 今天給 866 一個交付日並同步給 Quincy", you="只需確認今天有給出日期", heidi=False),
 dict(hi=False, who="Quincy Chen", key="JOBHUB-826", type="承諾日明天到期",
   signal="截止 08/28（明天 15:00 收期）・現況 In Progress・<b>計畫日 08-25 10:14 才寫入</b>（開工前 4 小時）",
   cause="計畫日期是開工當下才補的，因此「晚幾天開工」無法計算——但承諾日本身是明天",
   impact="這是 Quincy Goal 01 唯一一張 Goal Work",
   act="Quincy 今天回報 08/28 守不守得住", you="守不住時裁決縮哪一段範圍", heidi=True),
 dict(hi=False, who="Quincy Chen", key="JOBHUB-402", type="停在 DEV DONE 15 個工作天",
   signal="<b>08-06 14:38</b> 進 DEV DONE，至今未再轉態・從未進過 In Progress",
   cause="規格 08-05 已由 PM 拍板，卡的是驗收沒人做",
   impact="它被列在 Quincy 的 Goal 02（事後重建）。計畫日 08-19 才回填成 08-06，所以「逾期 21 天」是回填出來的假象——<b>真正的事實是它在 DEV DONE 躺了 15 個工作天（21 個日曆天）</b>",
   act="驗收目前無人承接（規格 08-05 已由你拍板）", you="指定驗收人，或裁決退回 Backlog", heidi=True),
 dict(hi=False, who="Lodifa Chen", key="JOBHUB-582", type="母卡已完成但子卡未完成",
   signal="582 於 08-26 10:40 轉 Done・子卡 <b>JOBHUB-728</b> 現況 In Progress（曾 Done→DEV DONE→Testing→In Progress 倒退）",
   cause="08-26 另開 JOBHUB-880（前端需重整才更新）",
   impact="Lodifa 的 Goal 說「推上 Production 環境」，但底下的後端 API 還在動",
   act="Lodifa 確認 728／880 是否影響上 Production", you="不影響就請她明講，讓 Goal 可以收掉", heidi=False),
]
NEEDYOU=[r for r in RISKS if r['heidi']]
A('<div class="sec"><div class="sech"><span class="n">04</span><h2>NEEDS ATTENTION</h2>'
  '<span class="hint">%d 項待處理，其中 <b style="color:var(--red)">%d 項需要你裁決</b></span></div>'
  %(len(RISKS),len(NEEDYOU)))
A('<div class="card pad" style="margin-bottom:12px">'
  '<div class="k" style="font-size:11px;letter-spacing:.1em;color:var(--tx3);margin-bottom:8px">'
  '今天需要你介入的</div><div class="pgl">%s</div></div>'
  %''.join('<a class="pgr red" href="#r-%s"><span class="gid2">%s</span>'
           '<span class="pgw">%s</span><span class="pgt">%s</span></a>'
           %(r['key'],r['key'][7:],esc(r['who'].split(' ')[0]),esc(r['you'])) for r in NEEDYOU))
for r in RISKS:
    A('<div class="risk%s" id="r-%s"><div class="rh"><span class="who">%s</span>%s'
      '<span class="tag %s">%s</span>%s</div><dl>'
      %(' hi' if r['hi'] else '',r['key'],esc(r['who']),L(r['key']),
        'bad' if r['hi'] else 'warn',esc(r['type']),
        ' <span class="tag bad">&#9873; 需要你裁決</span>' if r['heidi'] else
        ' <span class="tag">你只需知道</span>'))
    for lab,val in [("SIGNAL",r['signal']),("CAUSE",r['cause']),("IMPACT",r['impact']),
                    ("NEXT ACTION",r['act'])]:
        A('<dt>%s</dt><dd>%s</dd>'%(lab,val))
    A('<div class="yr"></div>')
    A('<dt class="you%s">%s</dt><dd class="you">%s</dd>'
      %('' if r['heidi'] else ' soft','你要裁決' if r['heidi'] else '你要知道',r['you']))
    A('</dl></div>')
A('<div class="faint" style="font-size:11.5px;margin-top:10px">'
  'SIGNAL 一律是 Jira 事實（欄位值或 changelog 時間戳）。CAUSE／IMPACT／NEXT ACTION 是判讀，'
  '看板不替任何人重排工作優先序。</div>')
A('</div>')


exec(open('contract.py',encoding='utf-8').read())

# ── SECTION 6 · ADDITIONAL DETAILS ──
A('<div class="sec"><div class="sech"><span class="n">06</span><h2>ADDITIONAL DETAILS</h2>'
  '<span class="hint">診斷資料 · 預設收合</span></div>')

partc=set(PARTICIPANTS)
other_all=[m for m in M if m['who'] in partc and m['key'] not in GOAL_WORK]
np_all=[m for m in M if m['who'] not in partc]

A('<div class="card"><details><summary>▸ Other Sprint Work（%d 張）— 在 Sprint 裡但未對應到任何已宣告的 Personal Goal</summary>'
  '<div class="pad"><div class="scroll"><table>'
  '<tr><th style="width:96px">KEY</th><th>TITLE</th><th style="width:96px">OWNER</th>'
  '<th style="width:104px">STATUS</th><th style="width:54px">PRI</th><th style="width:130px">PLAN</th></tr>%s'
  '</table></div><div class="faint" style="font-size:11.5px;margin-top:10px">'
  '這些卡<b>沒有被歸給任何 Goal，也沒有被推論歸屬</b>。它們存在本身就是 Planning discipline 的訊號：'
  '為什麼這張卡在 Sprint 裡，但不支撐任何人這週宣告要達成的事？<br>'
  'Lodifa 一人就佔 <b>%d</b> 張——數量大到值得直接問她本人，而不是由看板猜。</div></div></details>'
  %(len(other_all),
    ''.join('<tr><td>%s</td><td>%s</td><td class="dim">%s</td><td>%s</td><td class="dim">%s</td>'
            '<td class="mono faint">%s</td></tr>'
            %(L(m['key']),esc(m['sum']),esc(m['who']),stat(m['key']),esc(m['pri']),
              (m['pstart'] or '—')+' → '+(m['pend'] or '—'))
            for m in sorted(other_all,key=lambda x:(x['who'],x['key']))),
    sum(1 for m in other_all if m['who']=='Lodifa Chen')))

A('<details><summary>▸ 未指派的子卡（%d 張）— 母卡未指派 0 張，真正沒人的位置在子卡層</summary><div class="pad">'
  '<div class="scroll"><table><tr><th style="width:96px">KEY</th><th>TITLE</th>'
  '<th style="width:54px">PRI</th><th style="width:110px">母卡</th></tr>%s</table></div></div></details>'
  %(len(UNASSIGNED_SUBS),
    ''.join('<tr><td>%s</td><td>%s</td><td class="%s">%s</td><td class="dim">%s</td></tr>'
            %(L(x['key']),esc(x['sum']),'tag bad' if x['pri']=='P0' else 'dim',esc(x['pri']),L(x['parent']))
            for x in sorted(UNASSIGNED_SUBS,key=lambda y:y['key']))))

qa_par=[m for m in M if m['st']=='devdone']
qa_sub=[x for x in S if x['st']=='devdone']
A('<details><summary>▸ QA Queue（%d 張）— 狀態 DEV DONE，掛在開發者名下但實際是 QA 的待辦</summary><div class="pad">'
  '<div class="scroll"><table><tr><th style="width:96px">KEY</th><th style="width:52px">層級</th>'
  '<th>TITLE</th><th style="width:96px">原負責人</th></tr>%s%s</table></div>'
  '<div class="faint" style="font-size:11.5px;margin-top:10px">'
  'DEV DONE 在這個團隊<b>不等於可交付</b>——本期就有 JOBHUB-877 在 DEV DONE 被判複測未通過後退回 In Progress 的紀錄。</div>'
  '</div></details>'
  %(len(qa_par)+len(qa_sub),
    ''.join('<tr><td>%s</td><td class="faint">母卡</td><td>%s</td><td class="dim">%s</td></tr>'
            %(L(m['key']),esc(m['sum']),esc(m['who'])) for m in qa_par),
    ''.join('<tr><td>%s</td><td class="faint">子卡</td><td>%s</td><td class="dim">%s</td></tr>'
            %(L(x['key']),esc(x['sum']),esc(x['who'])) for x in qa_sub)))

A('<details><summary>▸ Non-participant Work（%d 張）— 不列入 Personal Goal execution</summary><div class="pad">'
  '<div class="scroll"><table><tr><th style="width:96px">KEY</th><th>TITLE</th>'
  '<th style="width:130px">OWNER</th><th style="width:104px">STATUS</th></tr>%s</table></div>'
  '<div class="faint" style="font-size:11.5px;margin-top:10px">'
  'Heidi Tsai 是 PM、陳語柔是外部資源，兩人不宣告 Personal Sprint Goal，'
  '名下工作列入 Sprint inventory 但不計入 execution。</div></div></details>'
  %(len(np_all),''.join('<tr><td>%s</td><td>%s</td><td class="dim">%s · %s</td><td>%s</td></tr>'
     %(L(m['key']),esc(m['sum']),esc(m['who']),NONPART.get(m['who'],''),stat(m['key'])) for m in np_all)))

A('<details><summary>▸ 今日 Sprint 範圍變動 — 3 張卡在 10:24 之後被移出 Sprint 14</summary><div class="pad">'
  '<div class="scroll"><table><tr><th style="width:96px">KEY</th><th>TITLE</th><th style="width:104px">移出時狀態</th></tr>'
  '<tr><td>%s</td><td>［調研］JobHub 職缺/履歷資料格式不同的存取方式</td><td>◕ Dev Done</td></tr>'
  '<tr><td>%s</td><td>［釐清］［B3］匯入精靈職缺選單：草稿可選與否</td><td>◐ In Progress</td></tr>'
  '<tr><td>%s</td><td>登出後按多次瀏覽器上一頁，出現誤導性錯誤畫面</td><td>○ To Do</td></tr>'
  '</table></div><div class="faint" style="font-size:11.5px;margin-top:10px">'
  '三張都是 Quincy 名下。移出後 Sprint 由 38 張變 35 張。</div></div></details>'
  %(L("JOBHUB-363"),L("JOBHUB-420"),L("JOBHUB-714")))

A('<details><summary>▸ Data Diagnostics — 資料來源與可信度</summary><div class="pad"><div class="scroll"><table>'
  '<tr><th style="width:180px">項目</th><th style="width:80px">性質</th><th>說明</th></tr>'
  '<tr><td>Jira 狀態／負責人／優先級／母子關係</td><td class="tag ok">事實</td><td>直接取自欄位。</td></tr>'
  '<tr><td>Actual Start / Actual End</td><td class="tag ok">事實</td>'
  '<td>取自 <code>changelog</code> 的狀態轉換時間戳。<b>Actual Start = 首次進 In Progress</b>；'
  '<b>Actual End = 首次進 Done</b>。DEV DONE <b>不</b>視為完成。'
  '402／825／877／363 從未進過 In Progress（直接 To Do→DEV DONE），因此 Actual Start 為空，已在表上標示。</td></tr>'
  '<tr><td>計畫日期可否比對</td><td class="tag ok">事實</td>'
  '<td>取自 <code>changelog</code> 中 <code>Start date</code>／<code>duedate</code> 欄位<b>被寫入的時間</b>。'
  '寫入時間早於 Sprint 開始、且早於這張卡任何執行事件 → <b>可比對</b>（本看板才畫計畫線、才計算延遲）；'
  '否則視為<b>事後補填</b>，只呈現事實。</td></tr>'
  '<tr><td>Personal Sprint Goal 文字</td><td class="tag ok">事實</td>'
  '<td>取自 <b>Jira 衝刺目標欄位</b>（sprint 8765 的 <code>goal</code>）。'
  '解析規則：編號開頭的行 → Team Goal；<code>姓名:一句話</code> 的行 → Personal Goal；'
  '同名多行 ＝ 多個 Goal。姓名用固定對照表換成 assignee 全名，<b>不做模糊比對</b>。'
  '本期 Quincy 的兩個 Goal 寫在同一行、以 <code>/</code> 分隔，'
  '而內文本身含 <code>/</code>，因此只能靠<b>句號＋斜線</b>切開——'
  '<span class="tag warn">寫法邊界不可靠</span>'
  'Quincy Goal 02 另標記為事後重建（該註記非取自 Jira，為 PO 註解）。</td></tr>'
  '<tr><td>Goal → Work 對應</td><td class="tag warn">人工提供</td>'
  '<td><b>唯一還沒有 Jira 來源的環節。</b>Goal 文字已入 Jira，但「哪幾張卡支撐這個 Goal」'
  '目前仍由人提供。<b>本看板不用 label／Epic 名稱／卡名／description 語意去推論歸屬</b>——'
  '沒有宣告的卡一律進 Other Sprint Work。</td></tr>'
  '<tr><td>CAUSE / IMPACT / NEED</td><td class="tag warn">判讀</td>'
  '<td>由留言與 changelog 判讀，非 Jira 結構化資料。</td></tr>'
  '<tr><td>Story point</td><td class="tag bad">不可用</td><td>全期 0 張填寫。</td></tr>'
  '<tr><td><code>Flagged</code></td><td class="tag bad">不可用</td>'
  '<td>全期 <b>0 張</b>設過，因此「誰在等誰」沒有任何結構化來源。</td></tr>'
  '<tr><td><code>issuelinks</code></td><td class="tag bad">幾乎不可用</td>'
  '<td>本期 35 張卡彼此之間<b>沒有任何一條登記的相依邊</b>。</td></tr>'
  '</table></div></div></details></div>')
A('</div>')

A('<div class="foot">'
  '這張看板回答的是「每個人這週承諾什麼、為此排了什麼、實際走到哪、偏差在哪、誰需要介入」。'
  '它不替工程師決定今天先做哪張卡。<br>'
  '卡住的時候：在該張 Jira 卡上把 <code>Flagged</code> 設成 <code>Impediment</code>。'
  '目前全期 0 張設過，所以上面每一條「在等什麼」都是判讀出來的。'
  '</div>')
A('</div>')
OUT = out_path()
_html = '\n'.join(O)
_dir = os.path.dirname(os.path.abspath(OUT))
if _dir:
    os.makedirs(_dir, exist_ok=True)
open(OUT,'w',encoding='utf-8').write(_html)
print("written", OUT, len(_html))
