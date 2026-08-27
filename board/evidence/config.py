# -*- coding: utf-8 -*-
"""Lifecycle 的所有可設定值。**不得把任何一個 hardcode 進 lifecycle function。**

改這個檔案不需要改邏輯；換國家、換 cadence、換上班時間都只動這裡。
"""

CONFIG = {
    # ── 時區 ──────────────────────────────────────────────────────────
    'timezone': 'Asia/Taipei',

    # ── 工作日 ────────────────────────────────────────────────────────
    # baseline：一週哪幾天算工作日（0=Mon … 6=Sun）
    'working_weekdays': [0, 1, 2, 3, 4],

    # 假日清單。**刻意留空**——台灣假日不寫死在程式裡。
    # 由使用端填入，或改用其他 provider（見 workday.py）。
    'holidays': [],

    # 額外工作日（補班日）。優先權高於 holidays 與 working_weekdays。
    'extra_working_days': [],

    # ── Lifecycle 判定 ────────────────────────────────────────────────
    # 收期時刻早於這個時間 → 當天沒有可用工時，最後工作日往前推一天
    'workday_start_time': '09:00',

    # T-1 當天轉入 SPRINT CLOSURE 的時刻
    'closure_checkpoint_time': '18:00',

    # 進入 CLOSING DECISION 的剩餘工作日數（含當天）
    'closing_decision_at_remaining_working_days': 2,

    # ── Layer D persistence ───────────────────────────────────────────
    # 承載人類裁決的 Jira system issue。append-only 留言。
    'decision_log_issue': 'JOBHUB-452',
    'decision_comment_marker': 'SPRINT-DECISION-V1',

    # ── 環境 ──────────────────────────────────────────────────────────
    'jira_cloud_id': '1406b31f-5391-412e-a7d5-a1c1ce4d1ac4',
    'jira_site': 'https://mayohumancapital.atlassian.net',
    'jira_project': 'JOBHUB',
    'jira_board_id': 1726,
}


def get(key, override=None):
    if override and key in override:
        return override[key]
    return CONFIG[key]
