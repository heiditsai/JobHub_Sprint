# JobHub 團隊看板

每日自動產生的 JOBHUB Sprint 團隊看板，由排程在 Anthropic 雲端環境產生後 `git push`，
由 Vercel 的 GitHub 整合自動部署。

## 網址結構

| 路徑 | 內容 |
| --- | --- |
| `/` | 今天的看板（每天覆蓋） |
| `/d/YYYY-MM-DD` | 當日封存版本（永久保留） |
| `/d/` | 封存索引 |

Teams 卡片永遠指向 `/`，Jira 每日快照留言可指向當天的 `/d/YYYY-MM-DD`。

## ⚠️ 這個站台目前是公開的

Vercel 免費方案部署出來的網址**任何人知道網址就能看**，即使 GitHub repo 是 private。
本看板包含同事姓名、卡片內容、阻塞分析與專案進度。

目前的減害措施只有「不被搜尋引擎索引」：

- `robots.txt` 全站 `Disallow`
- 每頁 `<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">`
- `vercel.json` 送出 `X-Robots-Tag` 與 `Referrer-Policy: no-referrer`

**這不等於存取控制。** 要真正擋人，兩個選項：

1. **Vercel Pro 的 Password Protection / SSO** — 真正的存取控制，需付費
2. **自寫密碼 middleware** — 免費，擋得住路人，但不是嚴謹的權限機制

## 部署設定（一次性）

1. 建一個 GitHub repo（建議 private）
2. Vercel → Add New Project → Import 這個 repo
3. Framework Preset 選 **Other**，Build Command 留空，Output Directory 留空（純靜態）
4. Deploy

之後每次 push 到 `main` 就會自動重新部署。

## 每日更新

排程每天產生新的 `index.html` 與 `d/YYYY-MM-DD.html`，commit 後 push。
git 歷史即為看板的版本紀錄，出錯可回溯。

## 資料來源與誠實標示

看板頁尾有完整的「哪些是真實 Jira 資料、哪些是示意、哪些是推論」對照表。
重點：

- Goal 歸屬是**每日重新推導**的，不沿用前一日結果
- 週曆日期多為**示意**（本專案母卡填「開始日期」者為 0 張）
- 阻塞關係優先採用 `issuelinks` 真實登記，沒有登記才讀留言推論並標明
- 刻意不使用 `updated` 欄位計算停滯天數（會被任何欄位變動刷新）
