import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QListWidget, QMessageBox, QLineEdit, QStatusBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class CopyThread(QThread):
    progress = pyqtSignal(str)  # 進捗表示用のカスタムシグナル
    finished = pyqtSignal()  # コピー完了を通知するシグナル

    def __init__(self, src_dirs, dest_dir):
        super().__init__()
        self.src_dirs = src_dirs
        self.dest_dir = dest_dir

    def run(self):
        try:
            for src_dir in self.src_dirs:
                dest_path = os.path.join(self.dest_dir, os.path.basename(src_dir))
                
                # コピー先に同じ名前のディレクトリがある場合はスキップ
                if os.path.exists(dest_path):
                    self.progress.emit(f"Skipping {src_dir}: already exists in destination.")
                    continue
                
                # コピー進捗を更新
                self.progress.emit(f"Copying {src_dir} to {dest_path}")

                # 非同期での `robocopy` 実行
                result = subprocess.run(
                    ['robocopy', src_dir, dest_path, '/E', '/NFL', '/NDL'],  # ファイル名・ディレクトリ名はログに出さない
                    capture_output=True,
                    text=True
                )

                # エラーコードを確認
                if result.returncode >= 8:  # robocopyでは8以上がエラー
                    raise Exception(f"robocopy error: {result.stdout}\n{result.stderr}")

            self.finished.emit()  # 完了通知
        except Exception as e:
            self.progress.emit(f"Error during copy: {str(e)}")


class DirectoryCopierApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_directories = []
        self.history_file = 'directory_selection_history.json'
        self.copy_thread = None

    def initUI(self):
        # ウィンドウの設定
        self.setWindowTitle('ディレクトリコピーアプリケーション')
        self.setGeometry(100, 100, 800, 600)

        # 全体レイアウトを設定
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        right_button_layout = QVBoxLayout()

        # 左側：選択されたディレクトリリスト
        self.selected_dirs_list = QListWidget(self)
        self.selected_dirs_list.setSelectionMode(QListWidget.MultiSelection)  # 複数選択を有効化
        top_layout.addWidget(self.selected_dirs_list, 3)  # 左側4分の3

        # 右側：ボタン類のレイアウト
        self.select_dir_button = QPushButton('ディレクトリを選択', self)
        self.select_dir_button.clicked.connect(self.openDirectoryDialog)
        right_button_layout.addWidget(self.select_dir_button)

        self.remove_dir_button = QPushButton('選択したディレクトリを削除', self)
        self.remove_dir_button.clicked.connect(self.removeSelectedDirectory)
        right_button_layout.addWidget(self.remove_dir_button)

        self.save_history_button = QPushButton('履歴を保存', self)
        self.save_history_button.clicked.connect(self.saveHistory)
        right_button_layout.addWidget(self.save_history_button)

        self.load_history_button = QPushButton('履歴を読み込み', self)
        self.load_history_button.clicked.connect(self.loadHistory)
        right_button_layout.addWidget(self.load_history_button)

        self.select_dest_dir_button = QPushButton('コピー先ディレクトリを選択', self)
        self.select_dest_dir_button.clicked.connect(self.selectDestDirectory)
        right_button_layout.addWidget(self.select_dest_dir_button)

        top_layout.addLayout(right_button_layout, 1)  # 右側4分の1

        # 下部：コピー先ディレクトリのパスとステータスバー
        bottom_layout = QVBoxLayout()
        self.dest_dir_display = QLineEdit(self)
        self.dest_dir_display.setReadOnly(True)
        bottom_layout.addWidget(self.dest_dir_display)

        self.copy_button = QPushButton('作業を開始', self)
        self.copy_button.clicked.connect(self.confirmAndStartCopy)
        bottom_layout.addWidget(self.copy_button)

        # ステータスバー
        self.status_bar = QStatusBar(self)
        bottom_layout.addWidget(self.status_bar)

        # メインレイアウトに追加
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        # レイアウトをウィジェットに設定
        self.setLayout(main_layout)

    def openDirectoryDialog(self):
        # ディレクトリ選択ダイアログを開く
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "ディレクトリを選択", "", options)
        
        if directory:
            # コピー先ディレクトリが選択されたディレクトリに含まれているかチェック
            if directory == self.dest_dir_display.text():
                QMessageBox.warning(self, "警告", "コピー先ディレクトリが選択されています。異なるディレクトリを選択してください。")
                return
            
            self.selected_directories.append(directory)
            self.updateSelectedDirsList()

    def updateSelectedDirsList(self):
        # 選択したディレクトリをリストウィジェットに表示
        self.selected_dirs_list.clear()
        self.selected_dirs_list.addItems(self.selected_directories)

    def removeSelectedDirectory(self):
        # リストウィジェットで選択された複数のディレクトリを削除
        selected_items = self.selected_dirs_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "削除するディレクトリを選択してください。")
            return
        for item in selected_items:
            self.selected_directories.remove(item.text())
        self.updateSelectedDirsList()

    def selectDestDirectory(self):
        # コピー先ディレクトリを選択
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "コピー先ディレクトリを選択", "", options)
        
        if directory:
            self.dest_dir_display.setText(directory)

    def confirmAndStartCopy(self):
        # コピー先ディレクトリが選択されたディレクトリの中にあるか確認
        dest_dir = self.dest_dir_display.text()
        if not dest_dir:
            QMessageBox.warning(self, "警告", "コピー先ディレクトリを指定してください。")
            return
        
        # コピー先ディレクトリが選択されたディレクトリのいずれかと一致するか確認
        for src_dir in self.selected_directories:
            if src_dir == dest_dir:
                QMessageBox.warning(self, "警告", f"コピー先ディレクトリと選択されたディレクトリが同じです。\n{src_dir}")
                return
        
        # コピーを実行する前に確認ポップアップを表示
        reply = QMessageBox.question(
            self, "確認", "自己責任、コピーを開始しますか？", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.startCopy()

    def startCopy(self):
        # コピー先ディレクトリの取得
        dest_dir = self.dest_dir_display.text()

        if not dest_dir:
            QMessageBox.warning(self, "警告", "コピー先ディレクトリを指定してください。")
            return

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # スレッドを使用してコピー作業を実行
        self.copy_thread = CopyThread(self.selected_directories, dest_dir)
        self.copy_thread.progress.connect(self.updateStatusBar)  # 進捗をステータスバーに反映
        self.copy_thread.finished.connect(self.copyFinished)  # コピー完了時に通知
        self.copy_thread.start()

    def updateStatusBar(self, message):
        self.status_bar.showMessage(message)

    def copyFinished(self):
        self.status_bar.showMessage("ディレクトリのコピーが完了しました。")
        QMessageBox.information(self, "完了", "ディレクトリのコピーが完了しました。")

    def saveHistory(self):
        # 選択されたディレクトリを履歴として保存
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.selected_directories, f, indent=4)
            QMessageBox.information(self, "保存完了", "履歴が保存されました。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"履歴の保存中にエラーが発生しました: {e}")

    def loadHistory(self):
        # 履歴ファイルからディレクトリリストを読み込み
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    self.selected_directories = json.load(f)
                self.updateSelectedDirsList()
                QMessageBox.information(self, "読み込み完了", "履歴が読み込まれました。")
            else:
                QMessageBox.warning(self, "警告", "履歴ファイルが見つかりません。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"履歴の読み込み中にエラーが発生しました: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DirectoryCopierApp()
    ex.show()
    sys.exit(app.exec_())
