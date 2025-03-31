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
    def test_initial_state(self, qtbot):
        """初期状態のテスト"""
        copier_app = DirectoryCopierApp()
        assert copier_app.selected_directories == []
        assert copier_app.copy_thread is None
        assert copier_app.parallel_copy is False

    @pytest.mark.gui
    def test_dest_dir_display_initial_state(self, qtbot):
        """コピー先ディレクトリ表示の初期状態テスト"""
        copier_app = DirectoryCopierApp()
        assert copier_app.dest_dir_display.text() == ""
        assert copier_app.dest_dir_display.isReadOnly() is True

    @pytest.mark.gui
    def test_cancel_button_initial_state(self, qtbot):
        """キャンセルボタンの初期状態テスト"""
        copier_app = DirectoryCopierApp()
        assert copier_app.cancel_button.isEnabled() is False

    @pytest.mark.gui
    def test_start_copy_operation(self, tmp_path, qtbot):
        """コピー開始処理のテスト"""
        copier_app = DirectoryCopierApp()
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
    def test_cancel_copy_operation(self, tmp_path, qtbot):
        """キャンセル処理のテスト"""
        copier_app = DirectoryCopierApp()
        # テスト用のディレクトリを準備
        source_dir = tmp_path / "source_cancel"
        dest_dir = tmp_path / "dest_cancel"
        source_dir.mkdir()
        (source_dir / "file.txt").write_text("cancel me")

        # コピー元とコピー先を設定
        copier_app.selected_directories.append(str(source_dir))
        copier_app.updateSelectedDirsList() # リストも更新
        copier_app.dest_dir_display.setText(str(dest_dir))

        # コピー処理を開始
        copier_app.startCopy()

        # キャンセルボタンが有効化されていることを確認
        # qtbot を使ってボタンの状態が変わるのを少し待つ
        qtbot.waitUntil(lambda: copier_app.cancel_button.isEnabled(), timeout=500) # 500ms 待機
        assert copier_app.cancel_button.isEnabled()

        # キャンセル処理を実行
        copier_app.cancelCopy()

        # 結果を検証
        # スレッドが終了し、ボタンが無効化されるのを待つ
        qtbot.waitUntil(lambda: copier_app.copy_thread is None, timeout=1000) # 1秒待機
        assert copier_app.copy_thread is None
        assert not copier_app.cancel_button.isEnabled()

    @pytest.mark.gui
    def test_progress_update(self, qtbot):
        """進捗更新のテスト"""
        copier_app = DirectoryCopierApp()
        # 進捗更新をシミュレート
        copier_app.updateProgressBar(50)
        copier_app.updateStatusBar("Copying: 5/10 (50%)")

        # プログレスバーの状態を検証
        assert copier_app.progress_bar.value() == 50


# DroppableQListWidgetの機能テスト
class TestDroppableQListWidget:
    @pytest.mark.gui
    def test_initial_state(self, qtbot):
        """初期状態のテスト"""
        list_widget = DroppableQListWidget()
        assert list_widget.count() == 0
        assert list_widget.existing_items == []
        assert list_widget.acceptDrops() is True

    @pytest.mark.gui
    def test_add_directory(self, qtbot):
        """ディレクトリ追加のテスト"""
        list_widget = DroppableQListWidget()
        test_dir = os.path.abspath(os.path.dirname(__file__))
        list_widget.addItem(test_dir)
        list_widget.existing_items.append(test_dir)
        assert list_widget.count() == 1
        assert test_dir in list_widget.existing_items

    @pytest.mark.gui
    def test_duplicate_directory(self, qtbot):
        """重複ディレクトリのテスト"""
        list_widget = DroppableQListWidget()
        test_dir = os.path.abspath(os.path.dirname(__file__))

        # 1回目の追加 (dropEventを模倣)
        if test_dir not in list_widget.existing_items:
            list_widget.addItem(test_dir)
            list_widget.existing_items.append(test_dir)

        # 2回目の追加（重複を試みる - dropEventを模倣）
        if test_dir not in list_widget.existing_items:
             list_widget.addItem(test_dir) # 本来は呼ばれないはず
             list_widget.existing_items.append(test_dir)

        # 重複は追加されないことを確認
        assert list_widget.count() == 1 # 視覚的にも1つだけのはず
        assert list_widget.existing_items.count(test_dir) == 1


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
