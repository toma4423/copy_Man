import sys
import os
import subprocess
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QMessageBox, QLineEdit
)
from PyQt5.QtCore import Qt

class DirectoryCopierApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.selected_directories = []
        self.history_file = 'directory_selection_history.json'

    def initUI(self):
        # ウィンドウの設定
        self.setWindowTitle('ディレクトリコピーアプリケーション')
        self.setGeometry(100, 100, 600, 500)

        # レイアウトの設定
        layout = QVBoxLayout()

        # ディレクトリ選択ボタン
        self.select_dir_button = QPushButton('ディレクトリを選択', self)
        self.select_dir_button.clicked.connect(self.openDirectoryDialog)
        layout.addWidget(self.select_dir_button)

        # 選択したディレクトリを表示するリストウィジェット
        self.selected_dirs_list = QListWidget(self)
        layout.addWidget(self.selected_dirs_list)

        # ディレクトリ削除ボタン
        self.remove_dir_button = QPushButton('選択したディレクトリを削除', self)
        self.remove_dir_button.clicked.connect(self.removeSelectedDirectory)
        layout.addWidget(self.remove_dir_button)

        # 履歴の保存ボタン
        self.save_history_button = QPushButton('履歴を保存', self)
        self.save_history_button.clicked.connect(self.saveHistory)
        layout.addWidget(self.save_history_button)

        # 履歴の読み込みボタン
        self.load_history_button = QPushButton('履歴を読み込み', self)
        self.load_history_button.clicked.connect(self.loadHistory)
        layout.addWidget(self.load_history_button)

        # コピー先ディレクトリ選択ボタン
        self.select_dest_dir_button = QPushButton('コピー先ディレクトリを選択', self)
        self.select_dest_dir_button.clicked.connect(self.selectDestDirectory)
        layout.addWidget(self.select_dest_dir_button)

        # コピー先ディレクトリを表示するテキストフィールド
        self.dest_dir_display = QLineEdit(self)
        self.dest_dir_display.setReadOnly(True)
        layout.addWidget(self.dest_dir_display)

        # コピー実行ボタン
        self.copy_button = QPushButton('作業を開始', self)
        self.copy_button.clicked.connect(self.startCopy)
        layout.addWidget(self.copy_button)

        # レイアウトをウィジェットに設定
        self.setLayout(layout)

    def openDirectoryDialog(self):
        # ディレクトリ選択ダイアログを開く
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "ディレクトリを選択", "", options)
        
        if directory:
            self.selected_directories.append(directory)
            self.updateSelectedDirsList()

    def updateSelectedDirsList(self):
        # 選択したディレクトリをリストウィジェットに表示
        self.selected_dirs_list.clear()
        self.selected_dirs_list.addItems(self.selected_directories)

    def removeSelectedDirectory(self):
        # リストウィジェットで選択されたディレクトリを削除
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

    def startCopy(self):
        # コピー先ディレクトリの取得
        dest_dir = self.dest_dir_display.text()

        if not dest_dir:
            QMessageBox.warning(self, "警告", "コピー先ディレクトリを指定してください。")
            return

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # `robocopy` を使用してディレクトリをコピー
        try:
            for src_dir in self.selected_directories:
                dest_path = os.path.join(dest_dir, os.path.basename(src_dir))
                
                # robocopyコマンドを実行
                result = subprocess.run(
                    ['robocopy', src_dir, dest_path, '/E', '/SL'],
                    capture_output=True,
                    text=True
                )

                # エラーコードを確認
                if result.returncode >= 8:  # robocopyでは8以上がエラー
                    raise Exception(f"robocopy error: {result.stdout}\n{result.stderr}")

            QMessageBox.information(self, "完了", "ディレクトリのコピーが完了しました。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"コピー中にエラーが発生しました: {e}")

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
