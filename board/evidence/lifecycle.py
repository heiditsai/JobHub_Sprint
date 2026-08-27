# -*- coding: utf-8 -*-
"""Sprint Lifecycle Engine —— 純函式。

輸入：sprint 的 startDate / endDate / state ＋ 工作日 provider ＋ 「現在」
輸出：lifecycle_state 與相關時間錨點

**它不讀 issue、不看 evidence、不做任何管理判斷，也不知道今天星期幾代表什麼。**
星期四 / 星期五只是目前 cadence 的偶然結果。
"""
from datetime import date, datetime, time, timedelta, timezone

NORMAL_EXECUTION = 'NORMAL_EXECUTION'
CLOSING_DECISION = 'CLOSING_DECISION'
FINAL_DAY_EXECUTION = 'FINAL_DAY_EXECUTION'
SPRINT_CLOSURE = 'SPRINT_CLOSURE'

STATES = [NORMAL_EXECUTION, CLOSING_DECISION, FINAL_DAY_EXECUTION, SPRINT_CLOSURE]

MANAGEMENT_QUESTION = {
    NORMAL_EXECUTION: '現在這個 Sprint 怎麼跑？',
    CLOSING_DECISION: '現在還有哪些 decision / action，如果今天處理，仍可能改變 Sprint outcome？',
    FINAL_DAY_EXECUTION: '經過昨天的 Closing Decisions 後，最後一天開始時，今天到底要守住什麼？',
    SPRINT_CLOSURE: '這個 Sprint 最後發生了什麼、前面的 Closing Decisions 結果如何、有什麼值得帶到下一期？',
}


# ── 時間工具 ──────────────────────────────────────────────────────────
def _tz(name):
    """只支援固定位移；Asia/Taipei 全年 UTC+8，不需要 tzdata。"""
    fixed = {'Asia/Taipei': 8, 'UTC': 0}
    if name not in fixed:
        raise ValueError('未支援的時區 %s；請擴充 _tz() 或改用 zoneinfo' % name)
    return timezone(timedelta(hours=fixed[name]))


def to_local(iso, tzname):
    if iso is None:
        return None
    s = iso.replace('Z', '+00:00')
    return datetime.fromisoformat(s).astimezone(_tz(tzname))


def _hhmm(s):
    h, m = s.split(':')
    return time(int(h), int(m))


# ── 時間錨點 ──────────────────────────────────────────────────────────
def anchors(sprint, cfg, wd):
    """回傳 sprint 的 lifecycle 時間錨點。

    last_working_day (T-1)：
        取 endDate 當地日期；**若收期時刻早於 workday_start_time，
        代表當天沒有可用工時 → 往前推一天**；再往前推到最近的工作日。
    second_last_working_day (T-2)：T-1 的前一個工作日。
    """
    tzname = cfg['timezone']
    start_local = to_local(sprint['startDate'], tzname)
    end_local = to_local(sprint['endDate'], tzname)

    d = end_local.date()
    shifted = False
    if end_local.timetz().replace(tzinfo=None) < _hhmm(cfg['workday_start_time']):
        d = d - timedelta(days=1)
        shifted = True

    t1 = wd.previous_working_day(d, inclusive=True)
    t2 = wd.previous_working_day(t1, inclusive=False)

    closure_at = datetime.combine(t1, _hhmm(cfg['closure_checkpoint_time']),
                                  tzinfo=_tz(tzname))
    return {
        'timezone': tzname,
        'sprint_start_local': start_local.isoformat(),
        'sprint_end_local': end_local.isoformat(),
        'end_time_shifted_back_a_day': shifted,
        'last_working_day': t1.isoformat(),
        'second_last_working_day': t2.isoformat(),
        'closure_checkpoint_at': closure_at.isoformat(),
        'total_working_days': wd.working_days_between(start_local.date(), t1),
    }


# ── 主函式 ────────────────────────────────────────────────────────────
def resolve(sprint, now, cfg, wd):
    """回傳 lifecycle 判定結果。

    sprint: {'id','name','state','startDate','endDate'}   —— 直接來自 Layer A
    now:    tz-aware datetime（當地時間）
    """
    a = anchors(sprint, cfg, wd)
    t1 = date.fromisoformat(a['last_working_day'])
    t2 = date.fromisoformat(a['second_last_working_day'])
    closure_at = datetime.fromisoformat(a['closure_checkpoint_at'])
    today = now.date()

    remaining = wd.working_days_between(today, t1) if today <= t1 else 0
    # working_days_between 兩端皆含；今天不是工作日時它不會把今天算進去
    if today > t1:
        remaining = 0

    single_day_sprint = (t2 < date.fromisoformat(a['sprint_start_local'][:10]))

    # 1) Sprint 已關閉 → 直接 CLOSURE（優先於一切）
    if sprint.get('state') == 'closed':
        state, reason = SPRINT_CLOSURE, 'sprint.state = closed'
    # 2) 已過 T-1 的 closure checkpoint
    elif now >= closure_at:
        state, reason = SPRINT_CLOSURE, '已到 T-1 %s checkpoint' % cfg['closure_checkpoint_time']
    # 3) 今天是 T-1，但還沒到 checkpoint
    elif today == t1:
        state, reason = FINAL_DAY_EXECUTION, '今天是最後一個工作日（T-1）'
    # 4) 今天是 T-2
    elif today == t2 and not single_day_sprint:
        state, reason = CLOSING_DECISION, '今天是倒數第二個工作日（T-2）'
    # 5) 其他
    else:
        state, reason = NORMAL_EXECUTION, '距收期還有 %d 個工作日' % remaining

    return {
        'lifecycle_state': state,
        'reason': reason,
        'now_local': now.isoformat(),
        'today': today.isoformat(),
        'remaining_working_days': remaining,
        'is_T1': today == t1,
        'is_T2': today == t2,
        'single_day_sprint': single_day_sprint,
        'closing_decision_window_skipped': single_day_sprint,
        'management_question': MANAGEMENT_QUESTION[state],
        'anchors': a,
        'config_used': {k: cfg[k] for k in
                        ('timezone', 'workday_start_time', 'closure_checkpoint_time',
                         'working_weekdays', 'closing_decision_at_remaining_working_days')},
    }
