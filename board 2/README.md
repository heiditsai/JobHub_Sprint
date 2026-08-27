# JobHub Sprint Board · 排程用程式碼

這個資料夾是給**無人值守的排程**下載用的。排程每天開一個全新容器，
拿不到任何本機檔案，所以程式碼放在這裡讓它 `curl`。

## 放哪裡

把整個 `board/` 資料夾放到 repo 根目錄，push 到 `main`。
Repo **必須是 public**（`raw.githubusercontent.com` 對 private repo 需要 token）。

    <repo>/
      board/
        FILES.txt        ← 要下載的檔案清單（新增檔案要一起更新）
        fetch.sh         ← 排程用的下載腳本
        evidence/*.py    ← Shared Evidence Layer + Lifecycle Engine
        gen2.py 等       ← Board renderer

## 排程怎麼用

    BOARD_REPO=<你的帳號>/<repo> bash <(curl -fsSL \
      https://raw.githubusercontent.com/<你的帳號>/<repo>/main/board/fetch.sh)

抓完之後的執行順序：

1. **抓 Jira**（這一步要 agent 用 MCP 做，Python 呼叫不到 MCP）
   落地成 `evidence/raw/issues_parent.json`、`issues_sub.json`、
   `changelog/all.json`
2. `python3 evidence/build.py` → `sprints/sprint-<n>/evidence.json`
3. `python3 evidence/lifecycle_run.py` → `lifecycle.json`（算出四態的哪一態）
4. `python3 gen2.py` → Board HTML
5. SendUserFile

## 自我檢查

    python3 evidence/test_lifecycle.py     # lifecycle 23 個案例
    python3 evidence/simulate_sprint14.py  # T-2 → T-1 → Closure 閉環

## 改程式碼

直接改這個資料夾、push。排程隔天自動用新版，不需要動排程設定。
新增檔案時**記得把檔名加進 `FILES.txt`**。
