# プラットフォーム別のテスト
import pytest
from mod.copy_support.win import WindowsCopy
from mod.copy_support.mac_linux import MacLinuxCopy
import os
import platform


def test_windows_copy(tmp_path):
    """Windowsのコピー処理テスト"""
    if platform.system() != "Windows":
        pytest.skip("Windows環境でのみ実行可能なテスト")

    # テスト用のディレクトリとファイルを作成
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    source_dir.mkdir()
    (source_dir / "test.txt").write_text("test content")

    def progress_callback(current, total, current_percent, total_percent):
        assert 0 <= current_percent <= 100

    copier = WindowsCopy(progress_callback)
    copier.copy(str(source_dir), str(dest_dir))  # 戻り値は期待しない

    # 代わりにファイルの存在を確認
    assert (dest_dir / "test.txt").exists()
    assert (dest_dir / "test.txt").read_text() == "test content"


def test_mac_linux_copy(tmp_path):
    """Mac/Linuxのコピー処理テスト"""
    if platform.system() == "Windows":
        pytest.skip("Mac/Linux環境でのみ実行可能なテスト")

    # テスト実装（同様の構造）
    pass
