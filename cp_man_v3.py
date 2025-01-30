import sys
import os
import json
from PyQt6.QtWidgets import (
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
    QTextEdit,
    QMenu,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from mod.copy_support import CopyManager
from mod.toma_logger import TomaLogger  # TomaLoggerをインポート
import concurrent.futures


# ロガーを初期化 (ログフォーマットやログディレクトリなどを指定)
logger = TomaLogger(log_name="copy_manager.log", log_dir="logs", log_format="text")


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
        self.copy_manager = CopyManager(self.report_progress, self.report_error)

    def run(self):
        try:
            total_dirs = len(self.src_dirs)
            if self.parallel_copy:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for i, src_dir in enumerate(self.src_dirs):
                        if self.cancelled:
                            self.progress.emit("コピーがキャンセルされました。")
                            logger.info("Copy canceled by user.")
                            break

                        dest_path = os.path.join(
                            self.dest_dir, os.path.basename(src_dir)
                        )
                        if os.path.exists(dest_path):
                            self.progress.emit(
                                f"Skipping {src_dir}: already exists in destination."
                            )
                            logger.info(f"Skipping {src_dir}: already exists.")
                            continue

                        self.progress.emit(f"Copying {src_dir} to {dest_path}")
                        logger.info(f"Copying {src_dir} to {dest_path}")
                        futures.append(
                            executor.submit(self.copy_manager.copy, src_dir, dest_path)
                        )

                    for future in concurrent.futures.as_completed(futures):
                        future.result()
            else:
                for i, src_dir in enumerate(self.src_dirs):
                    if self.cancelled:
                        self.progress.emit("コピーがキャンセルされました。")
                        logger.info("Copy canceled by user.")
                        break

                    dest_path = os.path.join(self.dest_dir, os.path.basename(src_dir))
                    if os.path.exists(dest_path):
                        self.progress.emit(
                            f"Skipping {src_dir}: already exists in destination."
                        )
                        logger.info(f"Skipping {src_dir}: already exists.")
                        continue

                    self.progress.emit(f"Copying {src_dir} to {dest_path}")
                    logger.info(f"Copying {src_dir} to {dest_path}")
                    self.copy_manager.copy(src_dir, dest_path)

            self.finished.emit()
            logger.info("Copy operation completed.")
        except Exception as e:
            error_msg = f"Error during copy: {str(e)}"
            self.progress.emit(error_msg)
            logger.error(error_msg)

    def report_progress(self, current, total, current_percent, total_percent):
        self.progress_percent.emit(int(total_percent))
        self.progress.emit(f"Copying: {current}/{total} ({current_percent}%)")
        logger.info(f"Progress: {current}/{total} ({current_percent}%)")

    def report_error(self, src, attempt, retries, message):
        self.progress.emit(f"Error copying {src}: {message}")
        logger.error(f"Error copying {src}: {message}")

    def cancel(self):
        self.cancelled = True


class DirectoryCopierApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_directories = []
        self.history_file = "directory_selection_history.json"
        self.copy_thread = None
        self.parallel_copy = False

    def initUI(self):
        self.setWindowTitle("copyMan_v3")
        self.setGeometry(100, 100, 600, 400)

        # メインレイアウト
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        right_button_layout = QVBoxLayout()

        # 選択されたディレクトリ表示リスト
        self.selected_dirs_list = QListWidget(self)
        self.selected_dirs_list.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
        )
        self.selected_dirs_list.setAcceptDrops(True)
        self.selected_dirs_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.selected_dirs_list.customContextMenuRequested.connect(self.showContextMenu)
        self.selected_dirs_list.dragEnterEvent = self.dragEnterEvent
        self.selected_dirs_list.dropEvent = self.dropEvent
        top_layout.addWidget(self.selected_dirs_list, 3)

        # ディレクトリ選択ボタン
        self.select_dir_button = QPushButton("ディレクトリを選択", self)
        self.select_dir_button.clicked.connect(self.openDirectoryDialog)
        right_button_layout.addWidget(self.select_dir_button)

        # 選択したディレクトリを削除ボタン
        self.remove_dir_button = QPushButton("選択したディレクトリを削除", self)
        self.remove_dir_button.clicked.connect(self.removeSelectedDirectory)
        right_button_layout.addWidget(self.remove_dir_button)

        # 履歴保存ボタン
        self.save_history_button = QPushButton("履歴を保存", self)
        self.save_history_button.clicked.connect(self.saveHistory)
        right_button_layout.addWidget(self.save_history_button)

        # 履歴読み込みボタン
        self.load_history_button = QPushButton("履歴を読み込み", self)
        self.load_history_button.clicked.connect(self.loadHistory)
        right_button_layout.addWidget(self.load_history_button)

        # コピー先ディレクトリ選択ボタン
        self.select_dest_dir_button = QPushButton("コピー先ディレクトリを選択", self)
        self.select_dest_dir_button.clicked.connect(self.selectDestDirectory)
        right_button_layout.addWidget(self.select_dest_dir_button)

        # 並列コピーオプション
        self.parallel_copy_checkbox = QCheckBox("並列コピーを有効にする", self)
        self.parallel_copy_checkbox.stateChanged.connect(self.toggleParallelCopy)
        right_button_layout.addWidget(self.parallel_copy_checkbox)

        top_layout.addLayout(right_button_layout, 1)

        # コピー先ディレクトリ表示エリア
        bottom_layout = QVBoxLayout()
        self.dest_dir_display = QLineEdit(self)
        self.dest_dir_display.setReadOnly(True)
        self.dest_dir_display.setAcceptDrops(True)
        self.dest_dir_display.dragEnterEvent = self.dragEnterEvent
        self.dest_dir_display.dropEvent = self.dropEvent
        bottom_layout.addWidget(self.dest_dir_display)

        # コピー開始ボタン
        self.copy_button = QPushButton("作業を開始", self)
        self.copy_button.clicked.connect(self.confirmAndStartCopy)
        bottom_layout.addWidget(self.copy_button)

        # プログレスバー
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

        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
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

    def openDirectoryDialog(self):
        # オプションを直接QFileDialog.Optionから設定
        options = QFileDialog.Option.ShowDirsOnly
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
        # オプションを直接QFileDialog.Optionから設定
        options = QFileDialog.Option.ShowDirsOnly
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
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

    def updateSelectedDirsList(self):
        self.selected_dirs_list.clear()
        self.selected_dirs_list.addItems(self.selected_directories)

    def toggleParallelCopy(self, state):
        self.parallel_copy = state == Qt.CheckState.Checked

    def showContextMenu(self, pos):
        menu = QMenu(self)
        remove_action = menu.addAction("選択を解除")
        remove_action.triggered.connect(self.removeSelectedDirectory)
        menu.exec(self.selected_dirs_list.mapToGlobal(pos))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DirectoryCopierApp()
    ex.show()
    sys.exit(app.exec())
