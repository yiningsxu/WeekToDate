# 日付変換ツール

報告週または和暦表記を `YYYY/MM/DD` 形式の西暦日付へ変換する、シンプルな静的 HTML ツールです。

`index.html` をブラウザで開くだけで利用できます。Python スクリプトから HTML を再生成したり、コマンドラインで単発変換することもできます。

## 機能

- JIHS/IDWR 形式の報告週を、その週の月曜日の日付へ変換
- 昭和・平成・令和の和暦表記を西暦日付へ変換
- 全角数字、全角英字、全角記号の入力を正規化
- 変換結果のコピー
- 入力例ボタン付きの静的 HTML UI
- 外部ライブラリ不要

## 対応する入力例

### 報告週

```text
2025年第1週
2025年第52週
2020年第53週
```

報告週は月曜日開始の ISO 週番号として扱います。第1週は 1月4日を含む週です。

例:

```text
2025年第1週 -> 2024/12/30
```

### 和暦

```text
昭和64年1月7日
平成31年4月30日
令和6年4月1日
H31.4.30
R6.4
```

日が省略された場合は、その月の1日として変換します。

例:

```text
R6.4 -> 2024/04/01
```

## 使い方

### ブラウザで使う

`index.html` をブラウザで開きます。

```bash
open index.html
```

GitHub Pages などに配置する場合も、`index.html` だけで動作します。

### HTML を再生成する

```bash
python3 generate_week_tool.py
```

標準では `index.html` が生成されます。出力先を指定する場合:

```bash
python3 generate_week_tool.py -o public/index.html
```

### コマンドラインで変換する

```bash
python3 generate_week_tool.py "2025年第1週"
python3 generate_week_tool.py "平成31年4月30日"
python3 generate_week_tool.py "R6.4"
```

出力例:

```text
2024/12/30
2019/04/30
2024/04/01
```

## ファイル構成

```text
.
├── generate_week_tool.py  # 変換ロジック、HTML 生成、CLI
├── index.html             # 公開用の静的 HTML サイト
└── README.md
```

## 参照元

- [JIHS IDWR 報告週対応表 2025年](https://id-info.jihs.go.jp/surveillance/idwr/calendar/2025/index.html)
- [JCB 和暦西暦早見表](https://www.jcb.co.jp/processing/share/wareki.html)

## 必要環境

- 静的サイトとして使う場合: モダンブラウザ
- HTML 生成または CLI 変換を行う場合: Python 3.9 以上

外部 Python パッケージは不要です。
