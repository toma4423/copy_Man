
# Copy Support Module

このモジュールは、Windows、macOS、Linux でのクロスプラットフォーム対応ファイルコピーを支援するツールです。  
特定の環境では Windows の `robocopy`、macOS/Linux では `rsync` を使用し、大量のファイルを効率的にコピーします。  
さらに、失敗したコピーに対してリトライ機能やリアルタイムでの進行状況を報告する機能を提供しています。
 
## 機能概要

- **クロスプラットフォーム対応**:  
  Windows では `robocopy`、macOS/Linux では `rsync` を使用してファイルをコピーします。
- **並列処理**:  
  複数のファイルやディレクトリを並列でコピーし、システムリソースを効率的に活用。
- **リトライ機能**:  
  コピーが失敗した場合、最大3回までリトライを行い、それでも失敗したファイルはログに記録します。
- **進行状況のリアルタイムフィードバック**:  
  ファイルコピーの進行状況をコールバック関数を通じてリアルタイムで報告します。
- **エラーハンドリング**:  
  存在しないファイルやアクセス権限がないファイルに対して、エラーを適切に処理し、ユーザーに通知します。

## 動作環境

- **Windows**: `robocopy` が必要です。Windows 10以降のOSでは標準インストールされています。
- **macOS/Linux**: `rsync` が必要です。最新バージョンを推奨します。

### 必要なインストール手順

#### macOS/Linux で `rsync` をインストールする方法

macOS/Linux では、`rsync` がインストールされていない場合、以下のコマンドでインストールできます。

**macOS**（Homebrew経由）:
```bash
brew install rsync
```

**Debian/Ubuntu系Linux**:
```bash
sudo apt-get install rsync
```

**RedHat/CentOS系Linux**:
```bash
sudo yum install rsync
```

## モジュールの使い方

以下は基本的な使用方法の例です。

### Pythonコードでの使用例

```python
from copy_support import CopyManager

# 進行状況を報告するためのコールバック関数
def progress_callback(copied_files, total_files, copied_bytes, total_bytes):
    print(f"進行状況: {copied_files}/{total_files} ファイルコピー完了")

# エラーが発生した際に呼び出されるコールバック関数
def error_callback(file, attempt, retries, error_message):
    print(f"エラー: {file}, 試行回数: {attempt}/{retries}, メッセージ: {error_message}")

# CopyManagerのインスタンスを作成
copy_manager = CopyManager(progress_callback, error_callback)

# コピー元とコピー先のパスを指定してファイルをコピー
copy_manager.copy('/path/to/source', '/path/to/destination')
```

## 注意事項

- **MacおよびLinuxでの拡張属性コピー**:  
  `rsync` の `-E` オプションを使用することで、拡張属性（ACL、リソースフォークなど）を保持します。拡張属性が必要な場合は、適切にオプションを設定してください。
  
- **ファイルのアクセス権限**:  
  コピー元またはコピー先のファイル/ディレクトリにアクセス権限がない場合、エラーが発生します。この場合は適切な権限を設定するか、管理者権限を使用してください。
