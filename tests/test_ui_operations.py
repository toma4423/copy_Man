import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import sys

# グローバルなQApplicationインスタンスを作成
app = QApplication(sys.argv)


@pytest.fixture(scope="session")
def qapp():
    """セッション全体で使用するQApplicationを提供"""
    yield app
    app.quit()


@pytest.fixture
def qtapp(qapp):
    """Qt Application fixture"""
    return qapp


@pytest.fixture
def copier_app(qapp, skip_gui):
    """DirectoryCopierAppのインスタンスを提供"""
    if skip_gui:
        pytest.skip("Skipping GUI test")
    from cp_man_v4 import DirectoryCopierApp

    window = DirectoryCopierApp()
    window.show()  # ウィンドウを表示
    qapp.processEvents()  # イベントを処理
    yield window
    window.close()
    qapp.processEvents()


class TestUIOperations:
    @pytest.mark.gui
    def test_parallel_copy_checkbox(self, copier_app, qapp):
        """並列コピーチェックボックスのテスト"""
        # 初期状態のテスト
        assert copier_app.parallel_copy is False

        # 状態を変更
        copier_app.parallel_copy = True
        qapp.processEvents()
        assert copier_app.parallel_copy is True

        # 状態を元に戻す
        copier_app.parallel_copy = False
        qapp.processEvents()
        assert copier_app.parallel_copy is False

    @pytest.mark.gui
    def test_directory_selection(self, copier_app, tmp_path, qapp):
        """ディレクトリ選択機能のテスト"""
        # テスト用ディレクトリの作成
        test_dir = str(tmp_path)

        # ディレクトリの選択をシミュレート
        copier_app.selected_directories.append(test_dir)
        copier_app.updateSelectedDirsList()
        qapp.processEvents()

        assert test_dir in copier_app.selected_directories
        assert copier_app.selected_dirs_list.count() == 1
