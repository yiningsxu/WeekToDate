# Date Conversion Tool

[日本語版はこちら](README.ja.md)

<p>
  <a href="https://yiningsxu.github.io/WeekToDate/"><kbd>Open Live Site</kbd></a>
</p>

A simple static HTML tool that converts Japanese reporting week labels, Gregorian date labels, or Japanese era date labels. The reporting-week panel can switch between week-to-date and date-to-week modes, and both modes show the infection season / epidemiological year.

You can use it by opening `index.html` in a browser. The Python script can also regenerate the HTML file or run one-off conversions from the command line.

## Features

- Convert JIHS/IDWR-style reporting weeks to the Monday date of that week
- Switch the reporting-week panel to convert Gregorian dates back to reporting year, week, and day
- Show the full Monday-Sunday date range for a reporting week
- Show the infection season week, using reporting week 36 as the season start
- Convert Showa, Heisei, and Reiwa era dates to Gregorian dates
- Normalize full-width digits, letters, and symbols
- Copy the main result, week/range details, and infection-season details
- Static responsive HTML UI with a dual-mode title switcher and mode-specific example buttons
- No external libraries required

## Supported Input Examples

### Reporting Weeks and Gregorian Dates

```text
2025年第1週
2025年第52週
2020年第53週
2025年1月1日
2025/1/1
2025-01-01
```

Reporting weeks are treated as Monday-start ISO week numbers. Week 1 is the week containing January 4.

In the browser UI, the first conversion panel starts in reporting-week-to-date mode. Use the `↔︎` button in the panel title to switch to date-to-reporting-week mode; the input label and example buttons update with the active mode.

The infection season starts at reporting week 36 and runs through week 35 of the following reporting year.

Example:

```text
2025年第1週 -> 2024/12/30
2025年第1週 -> 2025年第1週: 2024年12月30日 - 2025年1月5日
2025年第3週 -> 2024/2025 season, week 20
2025年1月1日 -> 2025年第1週第3日
2025年1月1日 -> 2024/2025 season, week 18
```

### Japanese Era Dates

```text
昭和64年1月7日
平成31年4月30日
令和6年4月1日
H31.4.30
R6.4
```

If the day is omitted, the tool converts the input as the first day of that month.

Example:

```text
R6.4 -> 2024/04/01
```

## Usage

### Use in a Browser

Open `index.html` in your browser.

```bash
open index.html
```

The site also works as-is on static hosting services such as GitHub Pages. The browser UI has one panel for reporting-week/date conversions and one panel for Japanese-era conversions.

### Regenerate the HTML

```bash
python3 generate_week_tool.py
```

By default, this writes `index.html`. To choose another output path:

```bash
python3 generate_week_tool.py -o public/index.html
```

### Convert from the Command Line

```bash
python3 generate_week_tool.py "2025年第1週"
python3 generate_week_tool.py "2025年1月1日"
python3 generate_week_tool.py "平成31年4月30日"
python3 generate_week_tool.py "R6.4"
```

Example output:

```text
2024/12/30
2025年第1週第3日 / 2024/2025シーズンの第18週
2019/04/30
2024/04/01
```

## Project Structure

```text
.
├── generate_week_tool.py  # Conversion logic, HTML generation, and CLI
├── index.html             # Static HTML site for publishing
├── README.md              # English README
└── README.ja.md           # Japanese README
```

## References

- [JIHS IDWR Reporting Week Calendar 2025](https://id-info.jihs.go.jp/surveillance/idwr/calendar/2025/index.html)
- [JCB Japanese Era / Gregorian Year Reference](https://www.jcb.co.jp/processing/share/wareki.html)

## Requirements

- Static site usage: a modern browser
- HTML generation or CLI conversion: Python 3.9 or later

No external Python packages are required.
