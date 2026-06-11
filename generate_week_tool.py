#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import date, timedelta
from pathlib import Path


SOURCE_URL = "https://id-info.jihs.go.jp/surveillance/idwr/calendar/2025/index.html"
WAREKI_SOURCE_URL = "https://www.jcb.co.jp/processing/share/wareki.html"
OUTPUT_FILE = Path("index.html")
SEASON_START_WEEK = 36
ERA_DEFINITIONS = {
    "令和": {"abbr": "R", "base_year": 2018, "start": date(2019, 5, 1), "end": None},
    "平成": {"abbr": "H", "base_year": 1988, "start": date(1989, 1, 8), "end": date(2019, 4, 30)},
    "昭和": {"abbr": "S", "base_year": 1925, "start": date(1926, 12, 25), "end": date(1989, 1, 7)},
}
ERA_BY_ABBR = {definition["abbr"]: name for name, definition in ERA_DEFINITIONS.items()}
FULLWIDTH_TRANSLATION = str.maketrans(
    "０１２３４５６７８９ＲｒＨｈＳｓ．。／－ー　",
    "0123456789RrHhSs../-- ",
)


def reporting_week_monday(year: int, week: int) -> date:
    """Return the Monday for a JIHS/IDWR reporting week.

    JIHS report-week correspondence tables use Monday-start ISO week numbering:
    week 1 is the week containing Jan 4, and some years have week 53.
    """
    return date.fromisocalendar(year, week, 1)


def weeks_in_reporting_year(year: int) -> int:
    return date(year, 12, 28).isocalendar().week


def infection_season_week(year: int, week: int) -> tuple[int, int, int]:
    """Return the infection season start/end years and week number.

    A season starts at reporting week 36 and runs through week 35 of the
    following reporting year.
    """
    if week >= SEASON_START_WEEK:
        season_start_year = year
        season_week = week - SEASON_START_WEEK + 1
    else:
        season_start_year = year - 1
        season_week = weeks_in_reporting_year(season_start_year) - SEASON_START_WEEK + 1 + week

    return season_start_year, season_start_year + 1, season_week


def format_infection_season(year: int, week: int) -> str:
    season_start_year, season_end_year, season_week = infection_season_week(year, week)
    return f"{season_start_year}/{season_end_year}シーズンの第{season_week}週"


def normalize_digits(value: str) -> str:
    return value.translate(FULLWIDTH_TRANSLATION)


def parse_reporting_week_label(value: str) -> tuple[int, int]:
    normalized = normalize_digits(value).strip()
    strict = re.fullmatch(r"(\d{4})\s*年\s*第?\s*(\d{1,2})\s*週", normalized)
    if strict:
        return int(strict.group(1)), int(strict.group(2))

    loose = re.search(r"(\d{4})\D+(\d{1,2})", normalized)
    if loose:
        return int(loose.group(1)), int(loose.group(2))

    raise ValueError("入力形式は '2025年第1週' のようにしてください。")


def convert_reporting_week_label(value: str) -> str:
    year, week = parse_reporting_week_label(value)
    max_week = weeks_in_reporting_year(year)
    if not 1 <= week <= max_week:
        raise ValueError(f"{year}年は第{max_week}週までです。")
    return reporting_week_monday(year, week).strftime("%Y/%m/%d")


def month_end_date(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def parse_wareki_label(value: str) -> tuple[str, int, int, int, bool]:
    normalized = normalize_digits(value).strip().replace(" ", "").upper()
    match = re.fullmatch(r"(令和|平成|昭和)(元|\d{1,3})年(\d{1,2})月(?:(\d{1,2})日?)?", normalized)
    era_name = None
    if not match:
        match = re.fullmatch(r"([RHS])(元|\d{1,3})[./-](\d{1,2})(?:[./-](\d{1,2}))?", normalized)
        if match:
            era_name = ERA_BY_ABBR[match.group(1)]

    if not match:
        raise ValueError("入力形式は '平成31年4月30日' または 'H31.4.30' のようにしてください。")

    if era_name is None:
        era_name = match.group(1)
        year_token = match.group(2)
        month_token = match.group(3)
        day_token = match.group(4)
    else:
        year_token = match.group(2)
        month_token = match.group(3)
        day_token = match.group(4)

    era_year = 1 if year_token == "元" else int(year_token)
    month = int(month_token)
    day_was_defaulted = day_token is None
    day = int(day_token or 1)

    if era_year < 1:
        raise ValueError("和暦の年数は1以上で入力してください。")

    if not 1 <= month <= 12:
        raise ValueError("実在する日付を入力してください。")

    return era_name, era_year, month, day, day_was_defaulted


def convert_wareki_label(value: str) -> str:
    era_name, era_year, month, day, day_was_defaulted = parse_wareki_label(value)
    era = ERA_DEFINITIONS[era_name]
    year = era["base_year"] + era_year

    try:
        converted = date(year, month, day)
    except ValueError as exc:
        raise ValueError("実在する日付を入力してください。") from exc

    start = era["start"]
    end = era["end"]

    if day_was_defaulted:
        month_start = date(year, month, 1)
        month_end = month_end_date(year, month)
        if month_end < start or (end is not None and month_start > end):
            raise ValueError(f"{era_name}{era_year}年{month}月は{era_name}の期間外です。")
    elif converted < start or (end is not None and converted > end):
        if end is None:
            raise ValueError(f"{era_name}は{start.strftime('%Y/%m/%d')}からです。")
        raise ValueError(
            f"{era_name}は{start.strftime('%Y/%m/%d')}から{end.strftime('%Y/%m/%d')}までです。"
        )

    return converted.strftime("%Y/%m/%d")


def convert_label(value: str) -> str:
    try:
        year, week = parse_reporting_week_label(value)
    except ValueError:
        return convert_wareki_label(value)

    max_week = weeks_in_reporting_year(year)
    if not 1 <= week <= max_week:
        raise ValueError(f"{year}年は第{max_week}週までです。")
    return reporting_week_monday(year, week).strftime("%Y/%m/%d")


def render_html() -> str:
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>日付変換ツール</title>
  <style>
    :root {{
      color-scheme: light;
      --paper: #f7f8f4;
      --surface: #ffffff;
      --ink: #15181c;
      --muted: #5f6873;
      --line: #d8ddd2;
      --line-strong: #9ca88e;
      --accent: #1f6f64;
      --accent-dark: #134c46;
      --accent-soft: #dceee9;
      --warn: #a13f28;
      --focus: #2457d6;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100dvh;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        linear-gradient(90deg, rgba(21, 24, 28, 0.035) 1px, transparent 1px),
        linear-gradient(180deg, rgba(21, 24, 28, 0.035) 1px, transparent 1px),
        var(--paper);
      background-size: 32px 32px;
      color: var(--ink);
      letter-spacing: 0;
    }}

    main {{
      width: min(1080px, calc(100% - 32px));
      min-height: 100dvh;
      margin: 0 auto;
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
      gap: 32px;
      align-items: center;
      padding: 48px 0;
    }}

    .overview {{
      display: grid;
      gap: 28px;
      align-content: center;
    }}

    .tools {{
      display: grid;
      gap: 18px;
    }}

    .kicker {{
      width: fit-content;
      padding: 6px 10px;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.62);
      color: var(--accent-dark);
      font-size: 0.82rem;
      font-weight: 700;
    }}

    h1 {{
      margin: 0;
      max-width: 10ch;
      font-size: clamp(2.7rem, 7vw, 6.2rem);
      line-height: 0.96;
      font-weight: 850;
      letter-spacing: 0;
    }}

    .lead {{
      max-width: 58ch;
      margin: 0;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.8;
    }}

    .calendar-band {{
      display: grid;
      grid-template-columns: repeat(7, minmax(32px, 1fr));
      gap: 6px;
      width: min(520px, 100%);
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.72);
    }}

    .day {{
      display: grid;
      min-height: 52px;
      place-items: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface);
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 750;
    }}

    .day:first-child {{
      background: var(--accent-soft);
      border-color: rgba(31, 111, 100, 0.38);
      color: var(--accent-dark);
    }}

    .tool {{
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: 0 20px 45px rgba(32, 45, 34, 0.12);
      overflow: hidden;
    }}

    .tool-header {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 20px;
      border-bottom: 1px solid var(--line);
      background: #fbfcf8;
    }}

    .tool-title {{
      margin: 0;
      font-size: 1rem;
      line-height: 1.4;
      font-weight: 800;
    }}

    .status {{
      align-self: start;
      min-width: 72px;
      padding: 5px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      text-align: center;
      font-size: 0.78rem;
      font-weight: 750;
      white-space: nowrap;
    }}

    .status.ok {{
      border-color: rgba(31, 111, 100, 0.32);
      background: var(--accent-soft);
      color: var(--accent-dark);
    }}

    .status.error {{
      border-color: rgba(161, 63, 40, 0.3);
      background: #fae5de;
      color: var(--warn);
    }}

    .panel {{
      display: grid;
      gap: 18px;
      padding: 20px;
    }}

    label {{
      display: grid;
      gap: 8px;
      color: var(--muted);
      font-size: 0.88rem;
      font-weight: 750;
    }}

    .input-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
    }}

    input {{
      width: 100%;
      min-height: 52px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      padding: 0 14px;
      background: #ffffff;
      color: var(--ink);
      font: inherit;
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: 0;
    }}

    input:focus {{
      outline: 3px solid rgba(36, 87, 214, 0.2);
      border-color: var(--focus);
    }}

    button {{
      min-height: 52px;
      border: 1px solid var(--accent-dark);
      border-radius: 8px;
      padding: 0 16px;
      background: var(--accent);
      color: #ffffff;
      font: inherit;
      font-weight: 800;
      cursor: pointer;
    }}

    button:hover {{
      background: var(--accent-dark);
    }}

    button:focus-visible {{
      outline: 3px solid rgba(36, 87, 214, 0.28);
      outline-offset: 2px;
    }}

    button:disabled {{
      border-color: var(--line);
      background: #e8ece5;
      color: var(--muted);
      cursor: not-allowed;
    }}

    .result {{
      display: grid;
      gap: 10px;
      min-height: 154px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(220, 238, 233, 0.55), rgba(255, 255, 255, 0.82));
    }}

    .result-label {{
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 750;
    }}

    .date-output {{
      margin: 0;
      min-height: 54px;
      color: var(--ink);
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: clamp(2rem, 6vw, 3.15rem);
      line-height: 1.05;
      font-weight: 850;
      overflow-wrap: anywhere;
    }}

    .meta {{
      margin: 0;
      min-height: 24px;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.55;
    }}

    .copy-detail-list {{
      display: grid;
      gap: 8px;
    }}

    .copy-detail {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
      min-height: 40px;
    }}

    .detail-copy {{
      min-height: 36px;
      padding: 0 12px;
      border-color: var(--line-strong);
      background: #ffffff;
      color: var(--accent-dark);
      font-size: 0.84rem;
    }}

    .detail-copy:hover:not(:disabled) {{
      border-color: var(--accent);
      background: var(--accent-soft);
    }}

    .quick-list {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 8px;
    }}

    .quick-list button {{
      min-height: 40px;
      border-color: var(--line);
      background: #ffffff;
      color: var(--accent-dark);
      font-size: 0.86rem;
    }}

    .quick-list button:hover {{
      border-color: var(--accent);
      background: var(--accent-soft);
    }}

    .source {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 10px;
      padding: 14px 20px;
      border-top: 1px solid var(--line);
      background: #fbfcf8;
      color: var(--muted);
      font-size: 0.82rem;
      line-height: 1.5;
    }}

    a {{
      color: var(--accent-dark);
      font-weight: 800;
      text-decoration-thickness: 0.08em;
      text-underline-offset: 0.18em;
    }}

    .visually-hidden {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}

    @media (max-width: 840px) {{
      main {{
        grid-template-columns: 1fr;
        align-items: start;
        padding: 28px 0;
      }}

      h1 {{
        max-width: 12ch;
      }}
    }}

    @media (max-width: 540px) {{
      main {{
        width: min(100% - 20px, 1080px);
        gap: 22px;
      }}

      .overview {{
        gap: 18px;
      }}

      .calendar-band {{
        grid-template-columns: repeat(7, minmax(28px, 1fr));
        gap: 4px;
      }}

      .day {{
        min-height: 42px;
        font-size: 0.74rem;
      }}

      .tool-header,
      .panel,
      .source {{
        padding-inline: 14px;
      }}

      .input-row {{
        grid-template-columns: 1fr;
      }}

      .copy-detail {{
        grid-template-columns: 1fr;
        gap: 6px;
      }}

      .detail-copy {{
        width: fit-content;
      }}

      .quick-list {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="overview" aria-labelledby="page-title">
      <div class="kicker">DATE / JIHS</div>
      <h1 id="page-title">日付 変換ツール</h1>
      <p class="lead">報告週から週の最初の月曜日へ、または昭和・平成・令和の和暦表記から西暦へ。報告週では第36週開始の感染症シーズン年も表示します。</p>
      <div class="calendar-band" aria-hidden="true">
        <span class="day">月</span>
        <span class="day">火</span>
        <span class="day">水</span>
        <span class="day">木</span>
        <span class="day">金</span>
        <span class="day">土</span>
        <span class="day">日</span>
      </div>
    </section>

    <div class="tools">
    <section class="tool" aria-label="報告週変換フォーム">
      <div class="tool-header">
        <p class="tool-title">週数から月曜日の日付へ</p>
        <output id="weekStatus" class="status">待機中</output>
      </div>

      <div class="panel">
        <label for="weekInput">
          入力
          <div class="input-row">
            <input id="weekInput" type="text" inputmode="text" autocomplete="off" value="2025年第1週" aria-describedby="weekMessage">
            <button id="weekCopyButton" type="button">コピー</button>
          </div>
        </label>

        <div class="result" aria-live="polite">
          <span class="result-label">出力</span>
          <p id="weekOutput" class="date-output">----</p>
          <div class="copy-detail-list">
            <div class="copy-detail">
              <p id="weekMessage" class="meta">入力すると自動で変換します。</p>
              <button id="weekRangeCopyButton" class="detail-copy" type="button" disabled>コピー</button>
            </div>
            <div class="copy-detail">
              <p id="weekSeasonMessage" class="meta">感染症シーズン年も表示します。</p>
              <button id="weekSeasonCopyButton" class="detail-copy" type="button" disabled>コピー</button>
            </div>
          </div>
        </div>

        <div class="quick-list" aria-label="入力例">
          <button type="button" data-week-example="2025年第1週">2025年第1週</button>
          <button type="button" data-week-example="2025年第52週">2025年第52週</button>
          <button type="button" data-week-example="2020年第53週">2020年第53週</button>
        </div>
      </div>

      <div class="source">
        <span>週は月曜日開始。感染症シーズンは第36週開始。</span>
        <a href="{SOURCE_URL}" target="_blank" rel="noopener">報告週対応表 2025年</a>
      </div>
    </section>

    <section class="tool" aria-label="和暦西暦変換フォーム">
      <div class="tool-header">
        <p class="tool-title">和暦から西暦の日付へ</p>
        <output id="eraStatus" class="status">待機中</output>
      </div>

      <div class="panel">
        <label for="eraInput">
          入力
          <div class="input-row">
            <input id="eraInput" type="text" inputmode="text" autocomplete="off" value="平成31年4月30日" aria-describedby="eraMessage">
            <button id="eraCopyButton" type="button">コピー</button>
          </div>
        </label>

        <div class="result" aria-live="polite">
          <span class="result-label">出力</span>
          <p id="eraOutput" class="date-output">----</p>
          <p id="eraMessage" class="meta">日が省略された場合は、その月の1日として変換します。</p>
        </div>

        <div class="quick-list" aria-label="入力例">
          <button type="button" data-era-example="昭和64年1月7日">昭和64年1月7日</button>
          <button type="button" data-era-example="平成31年4月30日">平成31年4月30日</button>
          <button type="button" data-era-example="R6.4">R6.4</button>
        </div>
      </div>

      <div class="source">
        <span>略号は S / H / R。日がない入力は月初に設定。</span>
        <a href="{WAREKI_SOURCE_URL}" target="_blank" rel="noopener">和暦西暦早見表</a>
      </div>
    </section>
    </div>
  </main>

  <script>
    const weekInput = document.querySelector("#weekInput");
    const weekOutput = document.querySelector("#weekOutput");
    const weekMessage = document.querySelector("#weekMessage");
    const weekSeasonMessage = document.querySelector("#weekSeasonMessage");
    const weekStatus = document.querySelector("#weekStatus");
    const weekCopyButton = document.querySelector("#weekCopyButton");
    const weekRangeCopyButton = document.querySelector("#weekRangeCopyButton");
    const weekSeasonCopyButton = document.querySelector("#weekSeasonCopyButton");
    const eraInput = document.querySelector("#eraInput");
    const eraOutput = document.querySelector("#eraOutput");
    const eraMessage = document.querySelector("#eraMessage");
    const eraStatus = document.querySelector("#eraStatus");
    const eraCopyButton = document.querySelector("#eraCopyButton");
    const ERAS = {{
      "令和": {{ abbr: "R", baseYear: 2018, start: "2019-05-01", end: null }},
      "平成": {{ abbr: "H", baseYear: 1988, start: "1989-01-08", end: "2019-04-30" }},
      "昭和": {{ abbr: "S", baseYear: 1925, start: "1926-12-25", end: "1989-01-07" }},
    }};
    const ERA_BY_ABBR = {{ R: "令和", H: "平成", S: "昭和" }};

    function normalizeDigits(value) {{
      return value
        .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xFEE0))
        .replace(/[Ｒ]/g, "R")
        .replace(/[ｒ]/g, "r")
        .replace(/[Ｈ]/g, "H")
        .replace(/[ｈ]/g, "h")
        .replace(/[Ｓ]/g, "S")
        .replace(/[ｓ]/g, "s")
        .replace(/[．。]/g, ".")
        .replace(/[／]/g, "/")
        .replace(/[－ー]/g, "-")
        .replace(/[　]/g, " ");
    }}

    function parseReportingWeek(value) {{
      const normalized = normalizeDigits(value).trim();
      const strict = normalized.match(/^(\\d{{4}})\\s*年\\s*第?\\s*(\\d{{1,2}})\\s*週$/);
      if (strict) {{
        return {{ year: Number(strict[1]), week: Number(strict[2]) }};
      }}

      const loose = normalized.match(/(\\d{{4}})\\D+(\\d{{1,2}})/);
      if (loose) {{
        return {{ year: Number(loose[1]), week: Number(loose[2]) }};
      }}

      return null;
    }}

    function mondayOfWeekOne(year) {{
      const jan4 = new Date(Date.UTC(year, 0, 4));
      const day = jan4.getUTCDay() || 7;
      jan4.setUTCDate(jan4.getUTCDate() - day + 1);
      return jan4;
    }}

    function weeksInReportingYear(year) {{
      const current = mondayOfWeekOne(year);
      const next = mondayOfWeekOne(year + 1);
      return Math.round((next - current) / (7 * 24 * 60 * 60 * 1000));
    }}

    function infectionSeasonWeek(year, week) {{
      const seasonStartWeek = {SEASON_START_WEEK};
      if (week >= seasonStartWeek) {{
        return {{
          startYear: year,
          endYear: year + 1,
          week: week - seasonStartWeek + 1,
        }};
      }}

      const startYear = year - 1;
      return {{
        startYear,
        endYear: year,
        week: weeksInReportingYear(startYear) - seasonStartWeek + 1 + week,
      }};
    }}

    function formatInfectionSeason(year, week) {{
      const season = infectionSeasonWeek(year, week);
      return `${{season.startYear}}/${{season.endYear}}シーズンの第${{season.week}}週`;
    }}

    function reportingWeekMonday(year, week) {{
      const start = mondayOfWeekOne(year);
      start.setUTCDate(start.getUTCDate() + (week - 1) * 7);
      return start;
    }}

    function formatDate(date) {{
      const year = date.getUTCFullYear();
      const month = String(date.getUTCMonth() + 1).padStart(2, "0");
      const day = String(date.getUTCDate()).padStart(2, "0");
      return `${{year}}/${{month}}/${{day}}`;
    }}

    function formatJapaneseDate(date) {{
      return `${{date.getUTCFullYear()}}年${{date.getUTCMonth() + 1}}月${{date.getUTCDate()}}日`;
    }}

    function setStatus(statusElement, kind, text) {{
      statusElement.className = `status ${{kind}}`;
      statusElement.textContent = text;
    }}

    function makeUtcDate(year, month, day) {{
      const candidate = new Date(Date.UTC(year, month - 1, day));
      if (
        candidate.getUTCFullYear() !== year ||
        candidate.getUTCMonth() + 1 !== month ||
        candidate.getUTCDate() !== day
      ) {{
        return null;
      }}
      return candidate;
    }}

    function isoToUtcDate(value) {{
      const [year, month, day] = value.split("-").map(Number);
      return makeUtcDate(year, month, day);
    }}

    function monthEndDate(year, month) {{
      return new Date(Date.UTC(year, month, 0));
    }}

    function parseWarekiDate(value) {{
      const normalized = normalizeDigits(value).trim().replace(/\\s+/g, "").toUpperCase();
      let match = normalized.match(/^(令和|平成|昭和)(元|\\d{{1,3}})年(\\d{{1,2}})月(?:(\\d{{1,2}})日?)?$/);
      let eraName;
      let eraYearToken;
      let monthToken;
      let dayToken;

      if (match) {{
        eraName = match[1];
        eraYearToken = match[2];
        monthToken = match[3];
        dayToken = match[4];
      }}

      if (!match) {{
        match = normalized.match(/^([RHS])(元|\\d{{1,3}})[.\\/-](\\d{{1,2}})(?:[.\\/-](\\d{{1,2}}))?$/);
        if (match) {{
          eraName = ERA_BY_ABBR[match[1]];
          eraYearToken = match[2];
          monthToken = match[3];
          dayToken = match[4];
        }}
      }}

      if (!match) {{
        return {{ error: "例: 平成31年4月30日 / H31.4.30" }};
      }}

      const era = ERAS[eraName];
      const eraYear = eraYearToken === "元" ? 1 : Number(eraYearToken);
      const month = Number(monthToken);
      const defaultedDay = !dayToken;
      const day = Number(dayToken || 1);

      if (eraYear < 1) {{
        return {{ error: "和暦の年数は1以上で入力してください。" }};
      }}

      if (month < 1 || month > 12) {{
        return {{ error: "実在する日付を入力してください。" }};
      }}

      const converted = makeUtcDate(era.baseYear + eraYear, month, day);
      if (!converted) {{
        return {{ error: "実在する日付を入力してください。" }};
      }}

      const start = isoToUtcDate(era.start);
      const end = era.end ? isoToUtcDate(era.end) : null;

      if (defaultedDay) {{
        const monthStart = makeUtcDate(converted.getUTCFullYear(), month, 1);
        const monthEnd = monthEndDate(converted.getUTCFullYear(), month);
        if (monthEnd < start || (end && monthStart > end)) {{
          return {{ error: `${{eraName}}${{eraYear}}年${{month}}月は${{eraName}}の期間外です。` }};
        }}
      }} else if (converted < start || (end && converted > end)) {{
        if (!end) {{
          return {{ error: `${{eraName}}は${{formatDate(start)}}からです。` }};
        }}
        return {{ error: `${{eraName}}は${{formatDate(start)}}から${{formatDate(end)}}までです。` }};
      }}

      return {{ date: converted, eraName, eraYear, month, day, defaultedDay }};
    }}

    function formatEraYear(eraYear) {{
      return eraYear === 1 ? "元" : String(eraYear);
    }}

    function setWeekDetailCopyEnabled(isEnabled) {{
      weekRangeCopyButton.disabled = !isEnabled;
      weekSeasonCopyButton.disabled = !isEnabled;
    }}

    function convertWeek() {{
      const parsed = parseReportingWeek(weekInput.value);

      if (!parsed) {{
        weekOutput.textContent = "----";
        weekMessage.textContent = "例: 2025年第1週";
        weekSeasonMessage.textContent = "感染症シーズン年も表示します。";
        setWeekDetailCopyEnabled(false);
        setStatus(weekStatus, "error", "形式確認");
        return;
      }}

      const {{ year, week }} = parsed;
      const maxWeek = weeksInReportingYear(year);

      if (year < 1900 || year > 2100) {{
        weekOutput.textContent = "----";
        weekMessage.textContent = "対応範囲は1900年から2100年です。";
        weekSeasonMessage.textContent = "----";
        setWeekDetailCopyEnabled(false);
        setStatus(weekStatus, "error", "範囲外");
        return;
      }}

      if (week < 1 || week > maxWeek) {{
        weekOutput.textContent = "----";
        weekMessage.textContent = `${{year}}年は第${{maxWeek}}週までです。`;
        weekSeasonMessage.textContent = "----";
        setWeekDetailCopyEnabled(false);
        setStatus(weekStatus, "error", "週番号");
        return;
      }}

      const monday = reportingWeekMonday(year, week);
      const sunday = new Date(monday);
      sunday.setUTCDate(sunday.getUTCDate() + 6);

      weekOutput.textContent = formatDate(monday);
      weekMessage.textContent = `${{year}}年第${{week}}週: ${{formatJapaneseDate(monday)}} - ${{formatJapaneseDate(sunday)}}`;
      weekSeasonMessage.textContent = formatInfectionSeason(year, week);
      setWeekDetailCopyEnabled(true);
      setStatus(weekStatus, "ok", "変換済");
    }}

    function convertEra() {{
      const parsed = parseWarekiDate(eraInput.value);

      if (parsed.error) {{
        eraOutput.textContent = "----";
        eraMessage.textContent = parsed.error;
        setStatus(eraStatus, "error", "形式確認");
        return;
      }}

      eraOutput.textContent = formatDate(parsed.date);
      if (parsed.defaultedDay) {{
        eraMessage.textContent = `日が省略されたため、${{parsed.eraName}}${{formatEraYear(parsed.eraYear)}}年${{parsed.month}}月1日として変換しました。`;
      }} else {{
        eraMessage.textContent = `${{parsed.eraName}}${{formatEraYear(parsed.eraYear)}}年${{parsed.month}}月${{parsed.day}}日: ${{formatJapaneseDate(parsed.date)}}`;
      }}
      setStatus(eraStatus, "ok", "変換済");
    }}

    async function copyText(value, statusElement, focusElement) {{
      const normalizedValue = value.trim();
      if (!normalizedValue || normalizedValue === "----") {{
        setStatus(statusElement, "error", "未変換");
        return;
      }}

      try {{
        await navigator.clipboard.writeText(normalizedValue);
        setStatus(statusElement, "ok", "コピー済");
      }} catch {{
        focusElement.focus();
        setStatus(statusElement, "ok", "選択可");
      }}
    }}

    async function copyOutput(outputElement, statusElement, focusElement) {{
      const value = outputElement.textContent.trim();
      if (!/^\\d{{4}}\\/\\d{{2}}\\/\\d{{2}}$/.test(value)) {{
        setStatus(statusElement, "error", "未変換");
        return;
      }}

      await copyText(value, statusElement, focusElement);
    }}

    weekInput.addEventListener("input", convertWeek);
    eraInput.addEventListener("input", convertEra);
    weekCopyButton.addEventListener("click", () => copyOutput(weekOutput, weekStatus, weekInput));
    weekRangeCopyButton.addEventListener("click", () => copyText(weekMessage.textContent, weekStatus, weekInput));
    weekSeasonCopyButton.addEventListener("click", () => copyText(weekSeasonMessage.textContent, weekStatus, weekInput));
    eraCopyButton.addEventListener("click", () => copyOutput(eraOutput, eraStatus, eraInput));
    document.querySelectorAll("[data-week-example]").forEach((button) => {{
      button.addEventListener("click", () => {{
        weekInput.value = button.dataset.weekExample;
        convertWeek();
        weekInput.focus();
      }});
    }});
    document.querySelectorAll("[data-era-example]").forEach((button) => {{
      button.addEventListener("click", () => {{
        eraInput.value = button.dataset.eraExample;
        convertEra();
        eraInput.focus();
      }});
    }});

    convertWeek();
    convertEra();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the date conversion HTML tool.")
    parser.add_argument("input", nargs="?", help="Convert a label such as 2025年第1週 or H31.4.30")
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()

    if args.input:
        print(convert_label(args.input))
        return

    args.output.write_text(render_html(), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
