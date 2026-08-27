# -*- coding: utf-8 -*-
"""LAYER C · 已裁定的 Closing Decision 結構（人在 interpretation layer 寫的）。

這裡放的是**決策問題的定義**：標題、涉及哪個 Goal、evidence 範圍、owner。
**不放任何 derived state** —— 「幾張未指派」「逾期幾天」一律由 evidence 當場 render。

decision_id 由 make_decision_id() 依本清單順序指派，因此順序即是 id 的來源，
不要為了排版調換順序。
"""

AUTHORED = {
    8765: [
        {
            'title': 'AI Tag Goal 最後收斂範圍',
            'goal_refs': ['B1'],
            'issue_scope': ['JOBHUB-771', 'JOBHUB-773', 'JOBHUB-774'],
            'owner': 'PO',
            'po_decision_required': True,
            'why_now': '可測平台落在 812 與 813。今天決定範圍還能改變明天 Demo 講什麼；'
                       '收期之後只剩事後描述。',
            'ask': {'to': 'Bill Wang',
                    'question': '787 今天能不能收？811／813／815 到收期能到什麼程度？'},
            'options': ['HOLD_SCOPE', 'REDUCE_SCOPE', 'CARRY_FORWARD'],
            'if_no_action': 'B1 以母卡 In Progress／DEV DONE 混合狀態進入收期；'
                            '「PM 與 QA 可以測試」是否成立沒有共識。',
        },
        {
            'title': '面試管理前端最後收斂範圍',
            'goal_refs': ['Q1'],
            'issue_scope': ['JOBHUB-826'],
            'owner': 'PO',
            'po_decision_required': True,
            'why_now': 'duedate 與收期是同一時刻，沒有緩衝；且這張卡沒有子卡，'
                       '完成度在 Jira 上不可見。今天問還能縮範圍。',
            'ask': {'to': 'Quincy Chen',
                    'question': '826 原 scope 守不守得住？守不住的話本期最小可交付是什麼？'},
            'options': ['HOLD_SCOPE', 'REDUCE_SCOPE', 'CARRY_FORWARD'],
            'if_no_action': 'Q1 是否達成在收期前無法評估，且失去唯一一次縮範圍的機會。',
        },
        {
            'title': '收期前 Goal Work 的驗證範圍',
            'goal_refs': ['B1', 'Q2'],
            'issue_scope': ['JOBHUB-801', 'JOBHUB-802', 'JOBHUB-807', 'JOBHUB-402'],
            'owner': 'PO',
            'po_decision_required': True,
            'why_now': '收期之後這些卡的狀態就固定了。哪些必須在收期前驗完、'
                       '哪些明確 carry forward，決定 Demo 的說法與 Closure 的基準。',
            'ask': None,
            'options': ['HOLD_SCOPE', 'REDUCE_SCOPE', 'CARRY_FORWARD'],
            'if_no_action': '完成數會夾雜 DEV DONE 與 Done 兩種狀態，'
                            'Demo 與 Closure 可能用不同口徑。',
        },
    ]
}

# BEFORE NEXT SPRINT：有 owner、有價值，但**不影響本期 outcome**，
# 因此不進 Closing Decision，也不需要 decision_id。
BEFORE_NEXT_SPRINT = {
    8765: [
        {'owner': 'Erica lh Lee',
         'action': '替 JOBHUB-866 補一個交付日並同步 Quincy',
         'why': '866 是 E1「使 Quincy 下週可以串接」的實際解鎖點，目前沒有截止日。'
                '它決定 Quincy 下週一能不能開始，但不影響 Sprint 14 outcome。'},
    ]
}
