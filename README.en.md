# Date Conversion Tool

A simple static HTML tool that converts Japanese reporting week labels or Japanese era date labels into Gregorian dates in `YYYY/MM/DD` format.

You can use it by opening `index.html` in a browser. The Python script can also regenerate the HTML file or run one-off conversions from the command line.

## Features

- Convert JIHS/IDWR-style reporting weeks to the Monday date of that week
- Convert Showa, Heisei, and Reiwa era dates to Gregorian dates
- Normalize full-width digits, letters, and symbols
- Copy conversion results
- Static HTML UI with example buttons
- No external libraries required

## Supported Input Examples

### Reporting Weeks

```text
2025年第1週
2025年第52週
2020年第53週
```

Reporting weeks are treated as Monday-start ISO week numbers. Week 1 is the week containing January 4.

Example:

```text
2025年第1週 -> 2024/12/30
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

The site also works as-is on static hosting services such as GitHub Pages.

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
python3 generate_week_tool.py "平成31年4月30日"
python3 generate_week_tool.py "R6.4"
```

Example output:

```text
2024/12/30
2019/04/30
2024/04/01
```

## Project Structure

```text
.
├── generate_week_tool.py  # Conversion logic, HTML generation, and CLI
├── index.html             # Static HTML site for publishing
├── README.md              # Japanese README
└── README.en.md           # English README
```

## References

- [JIHS IDWR Reporting Week Calendar 2025](https://id-info.jihs.go.jp/surveillance/idwr/calendar/2025/index.html)
- [JCB Japanese Era / Gregorian Year Reference](https://www.jcb.co.jp/processing/share/wareki.html)

## Requirements

- Static site usage: a modern browser
- HTML generation or CLI conversion: Python 3.9 or later

No external Python packages are required.
