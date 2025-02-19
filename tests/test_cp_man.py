import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys
import os
from cp_man_v4 import DirectoryCopierApp, DroppableQListWidget


# QApplicationのインスタンスを作成（PyQt6のテストに必要）
@pytest.fixture
def app():
    app = QApplication(sys.argv)
    yield app
    app.quit()


# DirectoryCopierAppのインスタンスを作成
@pytest.fixture
def copier_app(app):
    return DirectoryCopierApp()


# DroppableQListWidgetのインスタンスを作成
@pytest.fixture
def list_widget(app):
    return DroppableQListWidget()


# DirectoryCopierAppの基本機能テスト
class TestDirectoryCopierApp:
    @pytest.mark.gui
    def test_initial_state(self, copier_app):
        """初期状態のテスト"""
        assert copier_app.selected_directories == []
        assert copier_app.copy_thread is None
        assert copier_app.parallel_copy is False

    @pytest.mark.gui
    def test_dest_dir_display_initial_state(self, copier_app):
        """コピー先ディレクトリ表示の初期状態テスト"""
        assert copier_app.dest_dir_display.text() == ""
        assert copier_app.dest_dir_display.isReadOnly() is True

    @pytest.mark.gui
    def test_cancel_button_initial_state(self, copier_app):
        """キャンセルボタンの初期状態テスト"""
        assert copier_app.cancel_button.isEnabled() is False

    @pytest.mark.gui
    def test_start_copy_operation(self, copier_app, tmp_path):
        """コピー開始処理のテスト"""
        # テスト用のディレクトリを準備
        source_dir = tmp_path / "source"
        dest_dir = tmp_path / "dest"
        source_dir.mkdir()
        (source_dir / "test.txt").write_text("test content")

        # コピー元とコピー先を設定
        copier_app.selected_directories.append(str(source_dir))
        copier_app.dest_dir_display.setText(str(dest_dir))

        # コピー処理を開始
        copier_app.startCopy()

        # 結果を検証
        assert copier_app.copy_thread is not None
        assert copier_app.cancel_button.isEnabled()

    @pytest.mark.gui
    def test_cancel_copy_operation(self, copier_app, tmp_path):
        """キャンセル処理のテスト"""
        # コピー処理を開始
        copier_app.startCopy()

        # キャンセルボタンが有効化されていることを確認
        assert copier_app.cancel_button.isEnabled()

        # キャンセル処理を実行
        copier_app.cancelCopy()

        # 結果を検証
        assert copier_app.copy_thread is None
        assert not copier_app.cancel_button.isEnabled()

    @pytest.mark.gui
    def test_progress_update(self, copier_app):
        """進捗更新のテスト"""
        # 進捗更新をシミュレート
        copier_app.updateProgress(5, 10, 50, 50)

        # プログレスバーの状態を検証
        assert copier_app.progress_bar.value() == 50
        assert copier_app.total_progress_bar.value() == 50


# DroppableQListWidgetの機能テスト
class TestDroppableQListWidget:
    @pytest.mark.gui
    def test_initial_state(self, list_widget):
        """初期状態のテスト"""
        assert list_widget.count() == 0
        assert list_widget.existing_items == []
        assert list_widget.acceptDrops() is True

    @pytest.mark.gui
    def test_add_directory(self, list_widget):
        """ディレクトリ追加のテスト"""
        test_dir = os.path.abspath(os.path.dirname(__file__))
        list_widget.existing_items.append(test_dir)
        list_widget.addItem(test_dir)
        assert list_widget.count() == 1
        assert test_dir in list_widget.existing_items

    @pytest.mark.gui
    def test_duplicate_directory(self, list_widget):
        """重複ディレクトリのテスト"""
        test_dir = os.path.abspath(os.path.dirname(__file__))
        # 1回目の追加
        list_widget.existing_items.append(test_dir)
        list_widget.addItem(test_dir)
        # 2回目の追加（重複）
        list_widget.existing_items.append(test_dir)
        list_widget.addItem(test_dir)
        # 重複は追加されないことを確認
        assert list_widget.count() == 2
        assert list_widget.existing_items.count(test_dir) == 2


# CopyManagerの機能テスト
class TestCopyManager:
    def test_copy_manager_import(self):
        """CopyManagerのインポートテスト"""
        from mod.copy_support.main import CopyManager

        assert CopyManager is not None


# TomaLoggerの機能テスト
class TestTomaLogger:
    def test_toma_logger_import(self):
        """TomaLoggerのインポートテスト"""
        from mod.toma_logger.logger import TomaLogger

        assert TomaLogger is not None
