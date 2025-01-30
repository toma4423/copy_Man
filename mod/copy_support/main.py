import os
import platform
from typing import Callable

# プラットフォームによって異なるモジュールをインポート
if platform.system() == "Windows":
    from .win import WindowsCopy
else:
    from .mac_linux import MacLinuxCopy


class CopyManager:
    def __init__(
        self, progress_callback: Callable = None, error_callback: Callable = None
    ):
        """
        ファイルコピーを管理するクラス。

        Parameters:
        progress_callback (Callable): 進行状況を報告するコールバック関数
        error_callback (Callable): エラー発生時に呼び出されるコールバック関数
        """
        self.progress_callback = progress_callback
        self.error_callback = error_callback

        # プラットフォーム別のコピー実行クラスをインスタンス化
        if platform.system() == "Windows":
            self.copy_handler = WindowsCopy(progress_callback, error_callback)
        else:
            self.copy_handler = MacLinuxCopy(progress_callback, error_callback)

    def copy(self, src: str, dest: str):
        """
        ファイルやディレクトリをコピーする。

        Parameters:
        src (str): コピー元のパス
        dest (str): コピー先のパス
        """
        if not os.path.exists(src):
            raise FileNotFoundError(f"コピー元のパスが見つかりません: {src}")

        self.copy_handler.copy(src, dest)

    def set_progress_callback(self, callback: Callable):
        """
        進行状況コールバックを設定する。

        Parameters:
        callback (Callable): 進行状況を報告するためのコールバック関数
        """
        self.progress_callback = callback
        self.copy_handler.set_progress_callback(callback)

    def set_error_callback(self, callback: Callable):
        """
        エラー発生時のコールバックを設定する。

        Parameters:
        callback (Callable): エラーを報告するためのコールバック関数
        """
        self.error_callback = callback
        self.copy_handler.set_error_callback(callback)
