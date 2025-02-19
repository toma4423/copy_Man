import pytest
import os
import shutil
from mod.copy_support.main import CopyManager


@pytest.fixture
def temp_dirs(tmp_path):
    """テスト用の一時ディレクトリを作成"""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    source_dir.mkdir()
    dest_dir.mkdir()

    # テスト用のファイルを作成
    test_file = source_dir / "test.txt"
    test_file.write_text("test content")

    return source_dir, dest_dir


class TestCopyOperations:
    def test_copy_single_file(self, temp_dirs):
        """単一ファイルのコピーテスト"""
        source_dir, dest_dir = temp_dirs

        def progress_callback(current, total, current_percent, total_percent):
            print(f"Progress: {current}/{total} ({current_percent}%)")

        def error_callback(src, attempt, retries, message):
            print(f"Error: {message}")

        copy_manager = CopyManager(progress_callback, error_callback)
        copy_manager.copy(str(source_dir), str(dest_dir / source_dir.name))

        # コピー結果の検証
        copied_file = dest_dir / source_dir.name / "test.txt"
        assert copied_file.exists()
        assert copied_file.read_text() == "test content"
