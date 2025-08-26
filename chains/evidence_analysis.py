"""
Evidence Analysis Chain
- 讀取 `code/config.json` 取得遠端 Ollama（VLM）伺服器 `base_url` 與 `model`
- 從命令列參數或 `code/data` 目錄中挑選一張圖片
- 將圖片（以 base64 data URL 內嵌）與文字提示與系統提示組成多模態訊息並輸出結果

中文說明：
- 此檔為「證物分析」任務的範例 chain
- 支援單張圖片、資料夾多張圖片、自動掃描預設資料夾三種模式
- 為避免遠端伺服器無法存取本機檔案，圖片以 base64 data URL 方式傳遞
"""

import json
import sys
import base64
import mimetypes
import time
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 嘗試相對匯入；若以腳本直接執行失敗，則加入專案根目錄改用絕對匯入
try:
    from ..prompts.system_prompts import EVIDENCE_ANALYSIS_SYSTEM_PROMPT  # type: ignore
except Exception:
    PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT_FOR_IMPORT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORT))
    from prompts.system_prompts import EVIDENCE_ANALYSIS_SYSTEM_PROMPT  # type: ignore


# 專案根目錄下的設定與資料目錄（此檔案位於 code/chains/）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
DATA_DIR = PROJECT_ROOT / "data"
# 支援的圖片格式樣式（依序搜尋）
IMAGE_GLOBS = ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp")


def load_config() -> dict:
    """讀取專案設定檔（config.json）。"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def pick_image_from_data() -> Path:
    """從預設資料夾挑選第一張符合格式的圖片。"""
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")
    for pattern in IMAGE_GLOBS:
        results = sorted(DATA_DIR.glob(pattern))
        if results:
            return results[0]
    raise FileNotFoundError(f"No image found in {DATA_DIR} matching {IMAGE_GLOBS}")


def list_images_in_dir(directory: Path) -> list[Path]:
    """列出資料夾內所有符合格式的圖片清單（已排序）。"""
    images: list[Path] = []
    for pattern in IMAGE_GLOBS:
        images.extend(sorted(directory.glob(pattern)))
    return images


def file_path_to_data_url(image_path: str) -> str:
    """讀取本機圖片並轉為 base64 data URL（供遠端 VLM 使用）。"""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    mime, _ = mimetypes.guess_type(path.name)
    if mime is None:
        # 若無法判斷，退回為 octet-stream；常見圖片副檔名已在上方列出
        mime = "application/octet-stream"
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_chain(llm: ChatOllama):
    """以 ChatPromptTemplate 建立多模態 chain（system + human 文字與圖片）。"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", EVIDENCE_ANALYSIS_SYSTEM_PROMPT),
        (
            "human",
            [
                {"type": "text", "text": "{question}"},
                {"type": "image_url", "image_url": "{image_url}"},
            ],
        ),
    ])
    return prompt | llm | StrOutputParser()


def main() -> None:
    """主流程：
    1) 讀取設定並建立 LLM 與 chain
    2) 取得待處理圖片清單
    3) 逐張送入多模態提示並收集輸出
    4) 於結尾印出總耗時
    """
    # 讀取設定檔，取得遠端 Ollama 的 base_url 與模型名稱
    cfg = load_config()
    base_url = cfg.get("ollama", {}).get("base_url", "http://0.0.0.0:8888")
    model = cfg.get("ollama", {}).get("model", "mistral")

    # 建立 LLM 與 chain（輸出以純文字解析）
    llm = ChatOllama(model=model, base_url=base_url)
    chain = build_chain(llm)

    # 依參數決定處理單檔或整個資料夾；無參數則處理預設資料夾
    targets: list[Path]
    if len(sys.argv) >= 2:
        provided = Path(sys.argv[1])
        if provided.is_dir():
            targets = list_images_in_dir(provided)
        else:
            targets = [provided]
    else:
        targets = list_images_in_dir(DATA_DIR)

    if not targets:
        raise FileNotFoundError("找不到可處理的圖片，請確認路徑或 data 目錄內容。")

    # 總耗時計時器（使用 perf_counter 以獲得高解析度時間）
    start_total = time.perf_counter()
    for idx, img_path in enumerate(targets, start=1):
        print(f"\n=== 處理第 {idx} 張：{img_path} ===")
        # 將圖片轉為 data URL 再注入到 human 訊息
        image_url = file_path_to_data_url(str(img_path))
        result = chain.invoke(
            {
                "question": "請描述這張圖片的內容與重點。",
                "image_url": image_url,
            }
        )
        print(result)
    elapsed_total = time.perf_counter() - start_total
    print(f"\n=== 全部處理完成，總耗時：{elapsed_total:.2f} 秒 ===")


if __name__ == "__main__":
    main()
