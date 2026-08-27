# -*- coding: utf-8 -*-
"""可替換的工作日 provider。

lifecycle.py 只依賴 WorkdayProvider 這個介面，不知道假日從哪來。
要換成 Jira 的工作日設定、Google Calendar、或公司 HR 系統，
只要實作同樣三個方法再傳進去即可。
"""
from datetime import date, timedelta


class WorkdayProvider:
    """介面。三個方法就是全部。"""

    def is_working_day(self, d: date) -> bool:
        raise NotImplementedError

    def previous_working_day(self, d: date, inclusive: bool = False) -> date:
        raise NotImplementedError

    def working_days_between(self, a: date, b: date) -> int:
        """a → b 之間的工作日數，**兩端皆含**。b < a 時回傳負數。"""
        raise NotImplementedError


class ConfigWorkdayProvider(WorkdayProvider):
    """V1 實作：週間 baseline ＋ 可設定假日清單 ＋ 可設定補班日。

    holidays / extra_working_days 皆為 'YYYY-MM-DD' 字串清單。
    **不含任何國家的假日資料**——那是 config 的責任，不是這裡的。
    """

    MAX_SCAN_DAYS = 400   # 防呆：整年都不是工作日時不要無限迴圈

    def __init__(self, working_weekdays=None, holidays=None, extra_working_days=None):
        self.working_weekdays = set(working_weekdays if working_weekdays is not None
                                    else [0, 1, 2, 3, 4])
        self.holidays = {self._d(x) for x in (holidays or [])}
        self.extra = {self._d(x) for x in (extra_working_days or [])}

    @staticmethod
    def _d(x):
        if isinstance(x, date):
            return x
        return date(int(x[0:4]), int(x[5:7]), int(x[8:10]))

    def is_working_day(self, d):
        if d in self.extra:
            return True          # 補班日優先
        if d in self.holidays:
            return False
        return d.weekday() in self.working_weekdays

    def previous_working_day(self, d, inclusive=False):
        cur = d if inclusive else d - timedelta(days=1)
        for _ in range(self.MAX_SCAN_DAYS):
            if self.is_working_day(cur):
                return cur
            cur -= timedelta(days=1)
        raise ValueError('往前掃 %d 天都沒有工作日，請檢查 working_weekdays 與 holidays'
                         % self.MAX_SCAN_DAYS)

    def working_days_between(self, a, b):
        if b < a:
            return -self.working_days_between(b, a)
        n, cur = 0, a
        while cur <= b:
            if self.is_working_day(cur):
                n += 1
            cur += timedelta(days=1)
        return n


def from_config(cfg):
    return ConfigWorkdayProvider(
        working_weekdays=cfg['working_weekdays'],
        holidays=cfg['holidays'],
        extra_working_days=cfg['extra_working_days'])
