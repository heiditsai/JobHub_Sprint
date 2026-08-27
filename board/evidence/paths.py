# -*- coding: utf-8 -*-
"""Sprint 目錄解析。**不要把 sprint-14 寫死在任何地方。**

優先序：
  1. 環境變數 BOARD_SPRINT_DIR
  2. sprints/ 底下編號最大的 sprint-*
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sprint_dir(sprint_name=None):
    env = os.environ.get('BOARD_SPRINT_DIR')
    if env:
        return env
    if sprint_name:
        n = ''.join(ch for ch in sprint_name if ch.isdigit())
        if n:
            return os.path.join(ROOT, 'sprints', 'sprint-%s' % n)
    cands = glob.glob(os.path.join(ROOT, 'sprints', 'sprint-*'))
    if not cands:
        return os.path.join(ROOT, 'sprints', 'sprint-unknown')
    def num(p):
        m = re.search(r'sprint-(\d+)$', p)
        return int(m.group(1)) if m else -1
    return max(cands, key=num)


def evidence_path(sprint_name=None):
    return os.environ.get('BOARD_EVIDENCE',
                          os.path.join(sprint_dir(sprint_name), 'evidence.json'))


def lifecycle_path(sprint_name=None):
    return os.environ.get('BOARD_LIFECYCLE',
                          os.path.join(sprint_dir(sprint_name), 'lifecycle.json'))
