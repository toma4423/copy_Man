
# TomaLogger

TomaLogger は、Pythonプロジェクトに簡単に統合できる汎用的なログ管理モジュールです。様々な形式でログを記録でき、特にXMLとJSON形式のサポートにより、柔軟なログ管理や解析が可能です。

## 特徴

- テキスト形式、JSON形式、XML形式（インデント付き）でのログ出力が可能。
- 日ごとのログローテーション対応。
- ログのコンソール出力とファイル出力の両方に対応。
- Pythonの logging モジュールをベースに設計されており、既存のコードベースに簡単に統合可能。

## インストール

このモジュールをプロジェクトに追加するには、`toma_logger` ディレクトリをプロジェクトフォルダにコピーしてください。

## 使用方法

### 1. ロガーの初期化

TomaLogger クラスを使用して、ロガーを作成します。ログ形式を指定し、ログファイルの保存先を設定できます。

```python
from toma_logger import TomaLogger

# ロガーの初期化
logger = TomaLogger(log_name="project_log.log", log_dir="logs", log_format="json")

# ログ出力
logger.info("プロジェクトが開始されました")
logger.warning("警告メッセージ")
logger.error("エラーメッセージ")
```

### 2. JSON形式でのログ出力

```python
logger = TomaLogger(log_name="json_log.log", log_dir="logs", log_format="json")
logger.info("これはJSON形式のログです")
```

出力されるJSONログの例:

```json
{
    "timestamp": "2024-10-05 13:35:40,268",
    "name": "json_log.log",
    "level": "INFO",
    "message": "これはJSON形式のログです"
}
```

### 3. XML形式でのログ出力（インデント付き）

```python
logger = TomaLogger(log_name="xml_log.log", log_dir="logs", log_format="xml")
logger.error("これはXML形式のログです")
```

出力されるXMLログの例:

```xml
<?xml version="1.0" ?>
<entry>
  <timestamp>2024-10-05 13:35:40,268</timestamp>
  <name>xml_log.log</name>
  <level>ERROR</level>
  <message>これはXML形式のログです</message>
</entry>
```

## クラスメソッド

- `info(message)` - 情報レベルのログを記録。
- `warning(message)` - 警告レベルのログを記録。
- `error(message)` - エラーレベルのログを記録。
- `exception(message)` - 例外情報を含むエラーログを記録。

## ログフォーマットの選択

`log_format` には以下の値を指定できます:
- `text`（デフォルト）: テキスト形式でログを出力。
- `json`: JSON形式でログを出力。
- `xml`: インデント付きのXML形式でログを出力。

## ディレクトリ構成

```
my_project/
│
├── toma_logger/
│   ├── __init__.py
│   └── logger.py
│
└── main.py
```

- `toma_logger/` フォルダには、TomaLogger クラスを定義するファイルが含まれています。
- `main.py` はプロジェクト全体で TomaLogger を利用するサンプルです。

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。
