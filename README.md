# LangChain + Ollama VLM 專案範例

本專案示範如何使用 LangChain 與遠端 Ollama（支援 VLM 的多模態模型）進行「證物分析」任務，並提供可擴充的多任務 chain 架構。

## 功能特點
- 使用 `ChatPromptTemplate` 建立多模態 chain（文字 + 圖片）。
- 以 base64 data URL 內嵌圖片，適用於遠端推論環境。
- 支援：單張圖片、資料夾多張圖片、預設目錄批次處理。
- 系統提示集中管理，易於維護與版本控管。

## 環境需求
- Python 3.10+（建議）
- 已安裝且可連線的遠端 Ollama 服務（預設 `config.json` 內設定）

## 快速開始（Windows）
- 建議建立虛擬環境，避免套件版本衝突
```bash
cd "C:\MyDocuments\Leadtek Research\Products\AIDMS\Technical Survey\LangChain\code"
python -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```
- 設定連線與模型（見下節）後，放入測試圖片至 `code/data`
- 直接以模組方式執行（避免相對匯入問題）
```bash
python -m code.chains.evidence_analysis
```
> 注意：請從專案根目錄 `code/` 之外上一層執行，或確保當前工作目錄包含 `code` 模組（上述 `cd` 指令已設定）。

## 設定
編輯 `code/config.json`：
```json
{
  "ollama": {
    "base_url": "http://10.1.1.4:29693",
    "model": "mistral-small3.1:24b"
  }
}
```
- base_url：你的雲端/遠端 Ollama 位址
- model：VLM 模型名稱（請先於伺服器端拉取對應模型）

## 專案結構
```
code/
  chains/
    evidence_analysis.py       # 證物分析任務（多圖批次、chain 化）
    __init__.py
  prompts/
    system_prompts.py          # 系統提示集中管理（含中文註解）
    __init__.py
  data/                        # 測試圖片放置處（jpg/jpeg/png/webp/bmp）
  config.json                  # 連線與模型設定
  requirements.txt
  README.md
```

## 執行方式
- 預設處理 `code/data` 內所有圖片
```bash
python -m code.chains.evidence_analysis
```
- 指定資料夾（依序處理該資料夾內所有圖片）
```bash
python -m code.chains.evidence_analysis C:\path\to\images
```
- 指定單一圖片
```bash
python -m code.chains.evidence_analysis C:\path\to\image.jpg
```

### 參數與行為說明
- 若提供路徑且為資料夾：會依副檔名篩選 `*.jpg, *.jpeg, *.png, *.webp, *.bmp` 後逐張處理
- 若提供路徑且為檔案：只處理該圖片
- 若未提供參數：自動掃描 `code/data` 目錄
- 會將圖片轉為 base64 data URL 再送至遠端 VLM

### 範例輸出（節錄）
```text
=== 處理第 1 張：code\data\01.jpg ===
（模型回覆）

=== 處理第 2 張：code\data\02.jpg ===
（模型回覆）

=== 全部處理完成，總耗時：12.34 秒 ===
```

## 證物分析任務說明
- 系統提示放於 `prompts/system_prompts.py` 的 `EVIDENCE_ANALYSIS_SYSTEM_PROMPT`
- chain 設計（於 `chains/evidence_analysis.py`）：
  - system：載入上述系統提示
  - human：文字 `{question}` + 圖片 `{image_url}`（base64 data URL）
  - 使用 `StrOutputParser()` 解析純文字輸出

## 疑難排解（Troubleshooting）
- 無法 import/ModuleNotFoundError：
  - 請以模組方式執行：`python -m code.chains.evidence_analysis`
- 遠端無法讀取本機檔案：
  - 本專案已將圖片轉為 base64 data URL 內嵌傳遞，無需 `file://` 存取
- 連線錯誤或模型不存在：
  - 檢查 `config.json` 的 `base_url` 與 `model`，確認伺服器已拉取/可用
- 非支援的圖片格式：
  - 請將圖片轉為 `jpg/jpeg/png/webp/bmp` 之一

## 擴充多任務範例
- 新增任務：
  1. 於 `prompts/system_prompts.py` 新增對應的 SYSTEM_PROMPT 常數
  2. 於 `chains/` 新增 `your_task.py`，參考 `evidence_analysis.py` 建立 chain
  3. 於 README 新增說明與指令

## 版權與授權
- 本範例僅供學術與技術交流之用，請遵循各模型與資料來源的授權條款。
