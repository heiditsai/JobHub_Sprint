# -*- coding: utf-8 -*-
"""訊號 enum → 中文短標。**看板與 Teams 卡片共用同一份**，避免同一個訊號
在兩個地方長成兩種說法。

這裡只做「翻譯」，不新增、不合併、不重新定義任何訊號；
enum 的唯一來源是 evidence/derive.py。
"""

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
