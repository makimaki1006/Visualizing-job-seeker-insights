# -*- coding: utf-8 -*-
"""
既存の（アクティブ）Chrome を引き継ぎ、カード一覧から各項目を抽出して CSV に保存。
挙動時間は "正規分布（Gaussian）" ベースでランダム化し、人間に近い所作を再現。

機能:
- Chrome (--remote-debugging-port=9222) へ CDP 接続し、#js-app タブを自動選択（未検出時は先頭タブ）
- カード親コンテナ直下の子 div を列挙し、実在するカードのみ走査（nth-child(i)）
- クリック/スクロール/ホバー/読了時間を「ガウス分布＋クリッピング」で揺らぎ
- ページャ「次へ」クリックで全ページ巡回（多段フォールバック）
- 取得カラム: 年齢・性別/居住地/ID/ステータス/希望勤務地/希望勤務形態/希望入職時期/経歴/就業状況/希望職種/資格
- 出力: UTF-8 CSV (results.csv)

依存:
    pip install playwright
    python -m playwright install

起動手順（例: Windows）:
  1) すべての Chrome を終了
  2) start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
  3) 対象サイトにログインして #js-app が表示されるページを開く
  4) python scrape_members_gaussian.py
"""

import csv
import re
import sys
import time
import json
import math
import random
from contextlib import contextmanager
from typing import Dict, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import urllib.request


# =========================
# 設定群（ここを調整）
# =========================
REMOTE_DEBUGGING_PORT = 9222
MAX_PAGES = 999

# Playwright タイムアウト（ベース）
PER_ELEMENT_TIMEOUT_MS = 2500
CLICK_TIMEOUT_MS = 5000
INITIAL_LOAD_WAIT_SEC = 0.8

# 人間化スケール（全体速度の倍率。>1でゆっくり）
HUMAN_SCALE = 1.0  # 0.8～1.5 推奨

# --- 正規分布パラメータ群（mean, std, min_clip, max_clip） ---
# スクロール→要素が視界に入った直後の注視
GAUSS_ATTENTION_AFTER_SCROLL = (0.45, 0.18, 0.15, 1.2)
# マウスの一時停止（hover前後）
GAUSS_HOVER_PAUSE = (0.22, 0.08, 0.08, 0.6)
# 微小スクロールの滞在
GAUSS_TINY_SCROLL_PAUSE = (0.18, 0.10, 0.06, 0.5)
# ページャクリック前の下方向自然スクロール後の間
GAUSS_PRE_PAGER_SCROLL_PAUSE = (0.45, 0.18, 0.15, 1.2)
# ページ遷移後の待機
GAUSS_AFTER_NAV_PAUSE = (0.45, 0.20, 0.15, 1.5)
# カード読了時間（ベース）
GAUSS_CARD_READ_BASE = (0.55, 0.20, 0.20, 1.6)
# 文字数係数（50文字あたりの加算）
GAUSS_PER50CH = (0.35, 0.12, 0.10, 0.9)
# クリックディレイ（ms）
GAUSS_CLICK_DELAY_MS = (55, 18, 15, 120)
# 微小スクロール確率
TINY_SCROLL_PROB = 0.25
# 微小スクロールのピクセル
TINY_SCROLL_PIX_MIN = 160
TINY_SCROLL_PIX_MAX = 420
# マウス移動
MOUSE_MOVE_STEPS = 12
MOUSE_MOVE_JITTER = 8  # px

OUTPUT_CSV = "results.csv"


# =========================
# セレクタ（親と各フィールド）
# =========================
CARD_LIST_ROOT = (
    "#js-app > div > div > div > div > "
    "div.u-disp-table.u-wd-100p > main > div > div > div > "
    "div:nth-child(4) > div > "
    "div.o-content__inner.o-content__inner--mq-1000-searches > "
    "div:nth-child(3) > div > div:nth-child(2) > div > div"
)
# 各カード: f"{CARD_LIST_ROOT} > div:nth-child({i})"

FIELDS = {
    "age_gender": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__header > "
        "div.c-search-member-card__header-controls > div > p:nth-child(1)"
    ),
    "location": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__header > "
        "div.c-search-member-card__header-controls > div > p:nth-child(3)"
    ),
    "member_id": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__header > p"
    ),
    "status": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__header > div.c-search-member-card__tags"
    ),
    "desired_area": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(1) > "
        "div.c-search-member-card__column-content > "
        "div:nth-child(1) > div > p"
    ),
    "desired_workstyle": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(1) > "
        "div.c-search-member-card__column-content > "
        "div:nth-child(2) > p.c-search-member-card-text.c-search-member-card-text--value.c-search-member-card-text--multiline"
    ),
    "desired_start": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(1) > "
        "div.c-search-member-card__column-content > "
        "div:nth-child(3) > p.c-search-member-card-text.c-search-member-card-text--value.c-search-member-card-text--multiline"
    ),
    "career": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(2) > "
        "div.c-search-member-card__column-content.c-search-member-card__column-content--padded > "
        "div:nth-child(1) > p.c-search-member-card-text.c-search-member-card-text--value.c-search-member-card-text--multiline"
    ),
    "employment_status": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(2) > "
        "div.c-search-member-card__column-content.c-search-member-card__column-content--padded > "
        "div:nth-child(2) > p.c-search-member-card-text.c-search-member-card-text--value.c-search-member-card-text--multiline"
    ),
    "desired_job": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(3) > "
        "div.c-search-member-card__column-content.c-search-member-card__column-content--padded > "
        "div:nth-child(1)"
    ),
    "qualifications": (
        " > div.c-search-member-card__main-content > "
        "div.c-search-member-card__content > div:nth-child(3) > "
        "div.c-search-member-card__column-content.c-search-member-card__column-content--padded > "
        "div:nth-child(2)"
    ),
}

PAGINATION_SELECTORS = [
    (
        "#js-app > div > div > div > div > "
        "div.u-disp-table.u-wd-100p > main > div > div > div > "
        "div:nth-child(4) > div > "
        "div.o-content__inner.o-content__inner--mq-1000-searches > "
        "div:nth-child(3) > div > div:nth-child(3) > "
        "div > div.c-search-arround-table__right-area > ul > li.c-pagination__next > a"
    ),
    "li.c-pagination__next > a",
    "text=次",
    "text=next",
]


# =========================
# ガウス分布ユーティリティ
# =========================
def gauss_clip(mean: float, std: float, lo: float, hi: float) -> float:
    """正規分布からサンプルし、[lo, hi] にクリップ"""
    v = random.gauss(mean, std)
    if v < lo: v = lo
    if v > hi: v = hi
    return v

def gtime(params) -> float:
    """(mean, std, lo, hi) 秒を HUMAN_SCALE 倍して返す"""
    mean, std, lo, hi = params
    return gauss_clip(mean * HUMAN_SCALE, std * HUMAN_SCALE, lo * HUMAN_SCALE, hi * HUMAN_SCALE)

def gtime_ms(params) -> int:
    """(mean, std, lo, hi) ミリ秒（int）"""
    sec = gtime(params)
    return max(0, int(round(sec * 1000)))

def sleep_g(params):
    time.sleep(gtime(params))

def sleep_fixed(sec: float):
    time.sleep(sec * HUMAN_SCALE)


# =========================
# 共通ユーティリティ
# =========================
def get_cdp_websocket_url(port: int) -> str:
    url = f"http://localhost:{port}/json/version"
    with urllib.request.urlopen(url, timeout=3) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    ws = data.get("webSocketDebuggerUrl")
    if not ws:
        raise RuntimeError("webSocketDebuggerUrl が取得できません。Chrome を --remote-debugging-port=XXXX で起動してください。")
    return ws

def clean_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", s.strip())

@contextmanager
def playwright_sync():
    with sync_playwright() as p:
        yield p


# =========================
# CDP 接続 & タブ選択
# =========================
def connect_to_active_page(p, ws_endpoint: str):
    browser = p.chromium.connect_over_cdp(ws_endpoint)
    contexts = browser.contexts
    if not contexts:
        raise RuntimeError("CDP 接続は成功したが、コンテキストが見つかりません。対象 Chrome でページを開いてください。")

    candidate = None
    for ctx in contexts:
        for pg in ctx.pages:
            try:
                pg.wait_for_selector("#js-app", timeout=1000)
                candidate = pg
                break
            except PWTimeoutError:
                continue
        if candidate:
            break

    if not candidate:
        candidate = contexts[0].pages[0]
        sleep_fixed(INITIAL_LOAD_WAIT_SEC)

    return browser, candidate


# =========================
# DOM 操作用
# =========================
def count_cards(page) -> int:
    try:
        root = page.locator(CARD_LIST_ROOT)
        if root.count() == 0:
            return 0
        children = root.locator(":scope > div")
        return children.count()
    except Exception:
        return 0

def safe_inner_text(page, selector: str) -> str:
    try:
        loc = page.locator(selector)
        if loc.count() == 0:
            return ""
        return clean_text(loc.first.inner_text(timeout=PER_ELEMENT_TIMEOUT_MS))
    except Exception:
        return ""

def human_scroll_into_view(page, locator):
    try:
        locator.scroll_into_view_if_needed(timeout=PER_ELEMENT_TIMEOUT_MS)
        sleep_g(GAUSS_ATTENTION_AFTER_SCROLL)
        # 視界の上すぎを避ける微調整
        page.evaluate("window.scrollBy(0, -80);")
    except Exception:
        pass
    # 微小スクロール癖
    human_tiny_scroll(page)

def human_tiny_scroll(page):
    if random.random() < TINY_SCROLL_PROB:
        pixels = random.randint(TINY_SCROLL_PIX_MIN, TINY_SCROLL_PIX_MAX)
        try:
            page.evaluate(f"window.scrollBy(0, {pixels});")
        except Exception:
            pass
        sleep_g(GAUSS_TINY_SCROLL_PAUSE)

def human_mouse_move_to(page, locator):
    try:
        box = locator.bounding_box()
        if not box:
            return
        target_x = box["x"] + box["width"] * random.uniform(0.35, 0.65)
        target_y = box["y"] + box["height"] * random.uniform(0.35, 0.65)

        # 目線移動っぽい寄せ（開始点にジッター）
        start_x = target_x + random.randint(-120, 120)
        start_y = max(0, target_y - random.randint(60, 180))
        page.mouse.move(start_x, start_y, steps=max(1, int(MOUSE_MOVE_STEPS/3)))
        sleep_g(GAUSS_HOVER_PAUSE)

        for _ in range(MOUSE_MOVE_STEPS):
            nx = target_x + random.randint(-MOUSE_MOVE_JITTER, MOUSE_MOVE_JITTER)
            ny = target_y + random.randint(-MOUSE_MOVE_JITTER, MOUSE_MOVE_JITTER)
            page.mouse.move(nx, ny, steps=1)
            time.sleep(0.008 * HUMAN_SCALE)

        locator.hover()
        sleep_g(GAUSS_HOVER_PAUSE)
    except Exception:
        pass

def human_click(page, locator):
    human_mouse_move_to(page, locator)
    try:
        locator.click(timeout=CLICK_TIMEOUT_MS, delay=gtime_ms(GAUSS_CLICK_DELAY_MS))
    except Exception:
        # フォールバック: JS click
        try:
            locator.evaluate("el => el.click()")
        except Exception:
            pass
    sleep_g(GAUSS_HOVER_PAUSE)

def estimate_read_time(texts: Dict[str, str]) -> float:
    """カードのテキスト総量から読了時間をガウスで算出（秒）"""
    total_len = sum(len(v or "") for v in texts.values())
    base = gtime(GAUSS_CARD_READ_BASE)
    per50 = gtime(GAUSS_PER50CH)
    add = min(2.5 * HUMAN_SCALE, (total_len // 50) * per50)
    # さらに軽い揺らぎ
    jitter = gauss_clip(0.12 * HUMAN_SCALE, 0.08 * HUMAN_SCALE, 0.0, 0.35 * HUMAN_SCALE)
    return base + add + jitter


def natural_scroll_to_pager_and_click(page) -> bool:
    # 下へ数段階スクロール（自然さ重視）
    try:
        for _ in range(3):
            page.evaluate("window.scrollBy(0, document.body.scrollHeight * 0.33);")
            sleep_g(GAUSS_TINY_SCROLL_PAUSE)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    except Exception:
        pass
    sleep_g(GAUSS_PRE_PAGER_SCROLL_PAUSE)

    # 候補セレクタを順に試す
    for sel in PAGINATION_SELECTORS:
        try:
            loc = page.locator(sel)
            if loc.count() == 0:
                continue
            a = loc.first
            aria = a.get_attribute("aria-disabled")
            if aria and aria.lower() in ("true", "1"):
                return False
            human_scroll_into_view(page, a)
            human_mouse_move_to(page, a)
            a.click(timeout=CLICK_TIMEOUT_MS, delay=gtime_ms(GAUSS_CLICK_DELAY_MS))
            sleep_g(GAUSS_AFTER_NAV_PAUSE)
            return True
        except Exception:
            continue
    return False


# =========================
# 1カード抽出
# =========================
def extract_card(page, i: int, page_num: int) -> Dict[str, str]:
    base = f"{CARD_LIST_ROOT} > div:nth-child({i})"
    base_loc = page.locator(base)
    human_scroll_into_view(page, base_loc)

    data = {}
    for key, tail in FIELDS.items():
        data[key] = safe_inner_text(page, base + tail)

    # テキスト量に応じて読了時間
    read_sec = estimate_read_time(data)
    time.sleep(read_sec)

    data["page"] = str(page_num)
    data["card_index"] = str(i)
    return data


# =========================
# メイン
# =========================
def main():
    # 連続実行でも偏りすぎない軽い乱数シード
    random.seed(time.time())

    ws = get_cdp_websocket_url(REMOTE_DEBUGGING_PORT)
    with playwright_sync() as p:
        browser, page = connect_to_active_page(p, ws)

        try:
            page.wait_for_selector("#js-app", timeout=5000)
        except PWTimeoutError:
            pass
        sleep_fixed(INITIAL_LOAD_WAIT_SEC)

        fieldnames = [
            "page", "card_index",
            "age_gender", "location", "member_id", "status",
            "desired_area", "desired_workstyle", "desired_start",
            "career", "employment_status", "desired_job", "qualifications",
        ]

        total_rows = 0
        page_num = 1

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()

            while page_num <= MAX_PAGES:
                n = count_cards(page)
                if n <= 0:
                    break

                for i in range(1, n + 1):
                    row = extract_card(page, i, page_num)
                    writer.writerow(row)
                    total_rows += 1
                    # たまに小さくスクロール
                    human_tiny_scroll(page)

                if not natural_scroll_to_pager_and_click(page):
                    break
                page_num += 1

        print(f"done: pages={page_num}, rows={total_rows}, output={OUTPUT_CSV}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", repr(e))
        sys.exit(1)
