#!/usr/bin/env bash
# 排程用：把 board/ 底下的程式碼抓到當前目錄。
# 用法：BOARD_REPO=heiditsai/JobHub_Sprint BOARD_REF=main bash fetch.sh
set -euo pipefail
REPO="${BOARD_REPO:-heiditsai/JobHub_Sprint}"
REF="${BOARD_REF:-main}"
BASE="https://raw.githubusercontent.com/${REPO}/${REF}/board"

mkdir -p evidence
curl -fsSL "${BASE}/FILES.txt" -o FILES.txt
while read -r f; do
  [ -z "$f" ] && continue
  mkdir -p "$(dirname "$f")"
  curl -fsSL "${BASE}/${f}" -o "$f"
done < FILES.txt
echo "fetched $(wc -l < FILES.txt) files from ${REPO}@${REF}"
python3 -c "import ast,sys;[ast.parse(open(f,encoding='utf-8').read(),f) for f in open('FILES.txt').read().split()]" \
  && echo "syntax OK"
