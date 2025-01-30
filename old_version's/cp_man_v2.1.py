import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QListWidget,
    QMessageBox,
    QLineEdit,
    QStatusBar,
    QProgressBar,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import concurrent.futures


class CopyThread(QThread):
    progress = pyqtSignal(str)
    progress_percent = pyqtSignal(int)
    finished = pyqtSignal()
    cancelled = False

    def __init__(self, src_dirs, dest_dir, parallel_copy=False):
        super().__init__()
        self.src_dirs = src_dirs
        self.dest_dir = dest_dir
        self.parallel_copy = parallel_copy

    def run(self):
        try:
            total_dirs = len(self.src_dirs)
            if self.parallel_copy:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for i, src_dir in enumerate(self.src_dirs):
                        if self.cancelled:
                            self.progress.emit("コピーがキャンセルされました。")
                            break

                        dest_path = os.path.join(
                            self.dest_dir, os.path.basename(src_dir)
                        )
                        if os.path.exists(dest_path):
                            self.progress.emit(
                                f"Skipping {src_dir}: already exists in destination."
                            )
                            continue

                        self.progress.emit(f"Copying {src_dir} to {dest_path}")
                        futures.append(
                            executor.submit(
                                self.copy_directory, src_dir, dest_path, i, total_dirs
                            )
                        )

                    for future in concurrent.futures.as_completed(futures):
                        future.result()
            else:
                for i, src_dir in enumerate(self.src_dirs):
                    if self.cancelled:
                        self.progress.emit("コピーがキャンセルされました。")
                        break

                    dest_path = os.path.join(self.dest_dir, os.path.basename(src_dir))
                    if os.path.exists(dest_path):
                        self.progress.emit(
                            f"Skipping {src_dir}: already exists in destination."
                        )
                        continue

                    self.progress.emit(f"Copying {src_dir} to {dest_path}")
                    self.copy_directory(src_dir, dest_path, i, total_dirs)

            self.finished.emit()
        except Exception as e:
            self.progress.emit(f"Error during copy: {str(e)}")

    def copy_directory(self, src_dir, dest_path, index, total_dirs):
        retries = 0
        while retries < 3:
            result = subprocess.run(
                ["robocopy", src_dir, dest_path, "/E", "/NFL", "/NDL"],
                capture_output=True,
                text=True,
            )
            if result.returncode < 8:
                break
            retries += 1
            self.progress.emit(f"Retry {retries}/3 for {src_dir}")

        if result.returncode >= 8:
            error_msg = f"robocopy error after {retries} retries: {result.stdout}\n{result.stderr}"
            self.progress.emit(error_msg)
            raise Exception(error_msg)

        progress_percentage = int(((index + 1) / total_dirs) * 100)
        self.progress_percent.emit(progress_percentage)

    def cancel(self):
        self.cancelled = True


class DirectoryCopierApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_directories = []
        self.history_file = "directory_selection_history.json"
        self.copy_thread = None
        self.parallel_copy = False  # デフォルトは並列コピーオフ

    def initUI(self):
        self.setWindowTitle("copyMan_v2.1")
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        right_button_layout = QVBoxLayout()

        # 左側：選択したディレクトリリスト (ドラッグアンドドロップ対応)
        self.selected_dirs_list = QListWidget(self)
        self.selected_dirs_list.setSelectionMode(QListWidget.MultiSelection)
        self.selected_dirs_list.setAcceptDrops(True)
        self.selected_dirs_list.dragEnterEvent = self.dragEnterEvent
        self.selected_dirs_list.dropEvent = self.dropEvent
        top_layout.addWidget(self.selected_dirs_list, 3)

        # 右側：ボタン類
        self.select_dir_button = QPushButton("ディレクトリを選択", self)
        self.select_dir_button.clicked.connect(self.openDirectoryDialog)
        right_button_layout.addWidget(self.select_dir_button)

        self.remove_dir_button = QPushButton("選択したディレクトリを削除", self)
        self.remove_dir_button.clicked.connect(self.removeSelectedDirectory)
        right_button_layout.addWidget(self.remove_dir_button)

        self.save_history_button = QPushButton("履歴を保存", self)
        self.save_history_button.clicked.connect(self.saveHistory)
        right_button_layout.addWidget(self.save_history_button)

        self.load_history_button = QPushButton("履歴を読み込み", self)
        self.load_history_button.clicked.connect(self.loadHistory)
        right_button_layout.addWidget(self.load_history_button)

        self.select_dest_dir_button = QPushButton("コピー先ディレクトリを選択", self)
        self.select_dest_dir_button.clicked.connect(self.selectDestDirectory)
        right_button_layout.addWidget(self.select_dest_dir_button)

        # 並列コピーのスイッチ
        self.parallel_copy_checkbox = QCheckBox("並列コピーを有効にする", self)
        self.parallel_copy_checkbox.stateChanged.connect(self.toggleParallelCopy)
        right_button_layout.addWidget(self.parallel_copy_checkbox)

        top_layout.addLayout(right_button_layout, 1)

        # 下部：コピー先ディレクトリのパスとステータスバー
        bottom_layout = QVBoxLayout()
        self.dest_dir_display = QLineEdit(self)
        self.dest_dir_display.setReadOnly(True)
        self.dest_dir_display.setAcceptDrops(True)
        self.dest_dir_display.dragEnterEvent = self.dragEnterEvent
        self.dest_dir_display.dropEvent = self.dropEvent
        bottom_layout.addWidget(self.dest_dir_display)

        self.copy_button = QPushButton("作業を開始", self)
        self.copy_button.clicked.connect(self.confirmAndStartCopy)
        bottom_layout.addWidget(self.copy_button)

        # 進捗バー
        self.progress_bar = QProgressBar(self)
        bottom_layout.addWidget(self.progress_bar)

        # キャンセルボタン
        self.cancel_button = QPushButton("キャンセル", self)
        self.cancel_button.clicked.connect(self.cancelCopy)
        bottom_layout.addWidget(self.cancel_button)
        self.cancel_button.setEnabled(False)

        # ステータスバー
        self.status_bar = QStatusBar(self)
        bottom_layout.addWidget(self.status_bar)

        # メインレイアウトに追加
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    # ドラッグアンドドロップ用のイベント
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            directory = url.toLocalFile()
            if os.path.isdir(directory):
                if directory == self.dest_dir_display.text():
                    QMessageBox.warning(
                        self,
                        "警告",
                        "コピー先ディレクトリが選択されています。異なるディレクトリを選択してください。",
                    )
                    continue

                if self.sender() == self.selected_dirs_list:
                    self.selected_directories.append(directory)
                    self.updateSelectedDirsList()
                elif self.sender() == self.dest_dir_display:
                    self.dest_dir_display.setText(directory)

    def toggleParallelCopy(self, state):
        self.parallel_copy = state == Qt.Checked

    def openDirectoryDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(
            self, "ディレクトリを選択", "", options
        )

        if directory:
            if directory == self.dest_dir_display.text():
                QMessageBox.warning(
                    self,
                    "警告",
                    "コピー先ディレクトリが選択されています。異なるディレクトリを選択してください。",
                )
                return
            self.selected_directories.append(directory)
            self.updateSelectedDirsList()

    def updateSelectedDirsList(self):
        self.selected_dirs_list.clear()
        self.selected_dirs_list.addItems(self.selected_directories)

    def removeSelectedDirectory(self):
        selected_items = self.selected_dirs_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "警告", "削除するディレクトリを選択してください。"
            )
            return
        for item in selected_items:
            self.selected_directories.remove(item.text())
        self.updateSelectedDirsList()

    def selectDestDirectory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(
            self, "コピー先ディレクトリを選択", "", options
        )

        if directory:
            self.dest_dir_display.setText(directory)

    def confirmAndStartCopy(self):
        dest_dir = self.dest_dir_display.text()
        if not dest_dir:
            QMessageBox.warning(
                self, "警告", "コピー先ディレクトリを指定してください。"
            )
            return

        for src_dir in self.selected_directories:
            if src_dir == dest_dir:
                QMessageBox.warning(
                    self,
                    "警告",
                    f"コピー先ディレクトリと選択されたディレクトリが同じです。\n{src_dir}",
                )
                return

        reply = QMessageBox.question(
            self,
            "確認",
            "自己責任、コピーを開始しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.startCopy()

    def startCopy(self):
        dest_dir = self.dest_dir_display.text()

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        self.copy_thread = CopyThread(
            self.selected_directories, dest_dir, self.parallel_copy
        )
        self.copy_thread.progress.connect(self.updateStatusBar)
        self.copy_thread.progress_percent.connect(self.updateProgressBar)
        self.copy_thread.finished.connect(self.copyFinished)
        self.copy_thread.start()

        self.cancel_button.setEnabled(True)

    def cancelCopy(self):
        if self.copy_thread:
            self.copy_thread.cancel()
            self.cancel_button.setEnabled(False)

    def updateProgressBar(self, value):
        self.progress_bar.setValue(value)

    def updateStatusBar(self, message):
        self.status_bar.showMessage(message)

    def copyFinished(self):
        self.status_bar.showMessage("ディレクトリのコピーが完了しました。")
        self.cancel_button.setEnabled(False)
        QMessageBox.information(self, "完了", "ディレクトリのコピーが完了しました。")

    def saveHistory(self):
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.selected_directories, f, indent=4)
            QMessageBox.information(self, "保存完了", "履歴が保存されました。")
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", f"履歴の保存中にエラーが発生しました: {e}"
            )

    def loadHistory(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    self.selected_directories = json.load(f)
                self.updateSelectedDirsList()
                QMessageBox.information(
                    self, "読み込み完了", "履歴が読み込まれました。"
                )
            else:
                QMessageBox.warning(self, "警告", "履歴ファイルが見つかりません。")
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", f"履歴の読み込み中にエラーが発生しました: {e}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DirectoryCopierApp()
    ex.show()
    sys.exit(app.exec_())
